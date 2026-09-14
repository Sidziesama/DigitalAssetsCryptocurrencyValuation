from __future__ import annotations

import argparse
import csv
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from .crypto_h8_breadth_pilot import read_csv


def validate(spec: dict[str, Any], ledger: dict[str, Any]) -> None:
    if spec.get("schema_version") != 1 or spec.get("status") != "frozen_before_event_estimation":
        raise ValueError("unsupported mechanism event study specification")
    if not spec.get("events") or not spec.get("selection_rule") or not spec.get("interpretation"):
        raise ValueError("mechanism event study requires events, a selection rule, and interpretation guardrails")
    if spec["pre_window_days"] < spec["minimum_days_per_window"] or spec["post_window_days"] < spec["minimum_days_per_window"]:
        raise ValueError("window lengths must be at least the minimum days per window")
    ledger_index = {(e["asset_id"], e["code"], e["effective_from"]): e["value"] for e in ledger["events"]}
    for event in spec["events"]:
        expected = 1 if event["transition"] == "activation" else 0
        if event["transition"] not in {"activation", "suspension"}:
            raise ValueError(f"event {event['event_id']} has an invalid transition")
        for code in event["codes"]:
            key = (event["asset_id"], code, event["effective_from"])
            if ledger_index.get(key) != expected:
                raise ValueError(f"event {event['event_id']} does not match an effective-dated ledger event for {code}")


def parse(value: str) -> date:
    return date.fromisoformat(value)


def window_means(panel: dict[str, dict[date, dict[str, str]]], asset: str, outcome: str,
                 start: date, end: date) -> tuple[float | None, int]:
    values = [float(row[outcome]) for day, row in panel.get(asset, {}).items()
              if start <= day <= end and row.get(outcome) not in (None, "")]
    return (sum(values) / len(values) if values else None), len(values)


def did(panel: dict[str, dict[date, dict[str, str]]], treated: str, controls: list[str], outcome: str,
        event_day: date, pre: int, post: int, minimum: int) -> dict[str, Any] | None:
    pre_start, pre_end = event_day - timedelta(days=pre), event_day - timedelta(days=1)
    post_start, post_end = event_day + timedelta(days=1), event_day + timedelta(days=post)
    deltas: dict[str, float] = {}
    counts: dict[str, tuple[int, int]] = {}
    for asset in [treated, *controls]:
        pre_mean, pre_n = window_means(panel, asset, outcome, pre_start, pre_end)
        post_mean, post_n = window_means(panel, asset, outcome, post_start, post_end)
        counts[asset] = (pre_n, post_n)
        if pre_mean is None or post_mean is None or pre_n < minimum or post_n < minimum:
            if asset == treated:
                return None
            continue
        deltas[asset] = post_mean - pre_mean
    control_deltas = [deltas[asset] for asset in controls if asset in deltas]
    if not control_deltas:
        return None
    return {"treated_delta": deltas[treated], "control_mean_delta": sum(control_deltas) / len(control_deltas),
            "difference_in_differences": deltas[treated] - sum(control_deltas) / len(control_deltas),
            "controls_used": len(control_deltas), "treated_pre_days": counts[treated][0], "treated_post_days": counts[treated][1]}


def build(spec: dict[str, Any], ledger: dict[str, Any], rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    validate(spec, ledger)
    panel: dict[str, dict[date, dict[str, str]]] = {}
    for row in rows:
        panel.setdefault(row["asset_id"], {})[parse(row["date"])] = row
    if not panel:
        raise ValueError("mechanism event study requires a non-empty panel")
    all_days = [day for days in panel.values() for day in days]
    panel_start, panel_end = min(all_days), max(all_days)
    pre, post, minimum = spec["pre_window_days"], spec["post_window_days"], spec["minimum_days_per_window"]
    results: list[dict[str, Any]] = []
    for event in spec["events"]:
        event_day = parse(event["effective_from"])
        window_start, window_end = event_day - timedelta(days=pre), event_day + timedelta(days=post)
        if window_start < panel_start or window_end > panel_end:
            raise ValueError(f"event {event['event_id']} window falls outside the frozen panel")
        contaminated = {e["asset_id"] for e in ledger["events"] if window_start <= parse(e["effective_from"]) <= window_end}
        controls = sorted(asset for asset in panel if asset != event["asset_id"] and asset not in contaminated)
        if not controls:
            raise ValueError(f"event {event['event_id']} has no uncontaminated control assets")
        for outcome in spec["outcomes"]:
            observed = did(panel, event["asset_id"], controls, outcome, event_day, pre, post, minimum)
            if observed is None:
                raise ValueError(f"event {event['event_id']} lacks sufficient {outcome} observations")
            asset_placebos = []
            for placebo in controls:
                pool = [asset for asset in [event["asset_id"], *controls] if asset != placebo]
                estimate = did(panel, placebo, pool, outcome, event_day, pre, post, minimum)
                if estimate is not None:
                    asset_placebos.append(estimate["difference_in_differences"])
            observed_value = observed["difference_in_differences"]
            asset_pool = [observed_value, *asset_placebos]
            date_placebos = []
            step = spec["date_placebo_step_days"]
            shift = step
            while True:
                placebo_day = event_day - timedelta(days=shift)
                if placebo_day - timedelta(days=pre) < panel_start:
                    break
                if placebo_day + timedelta(days=post) < window_start:
                    estimate = did(panel, event["asset_id"], controls, outcome, placebo_day, pre, post, minimum)
                    if estimate is not None:
                        date_placebos.append(estimate["difference_in_differences"])
                shift += step
            shift = step
            while True:
                placebo_day = event_day + timedelta(days=shift)
                if placebo_day + timedelta(days=post) > panel_end:
                    break
                if placebo_day - timedelta(days=pre) > window_end:
                    estimate = did(panel, event["asset_id"], controls, outcome, placebo_day, pre, post, minimum)
                    if estimate is not None:
                        date_placebos.append(estimate["difference_in_differences"])
                shift += step
            date_pool = [observed_value, *date_placebos]
            results.append({
                "event_id": event["event_id"], "asset_id": event["asset_id"], "codes": "|".join(event["codes"]),
                "transition": event["transition"], "expected_sign": event["expected_sign"], "effective_from": event["effective_from"],
                "outcome": outcome, "controls": "|".join(controls), **observed,
                "sign_matches_expectation": int((observed_value > 0) == (event["expected_sign"] == "positive")),
                "asset_placebos": len(asset_placebos),
                "asset_placebo_p_two_sided": sum(abs(v) >= abs(observed_value) - 1e-12 for v in asset_pool) / len(asset_pool),
                "asset_placebo_rank": sum(abs(v) > abs(observed_value) + 1e-12 for v in asset_placebos) + 1,
                "date_placebos": len(date_placebos),
                "date_placebo_p_two_sided": sum(abs(v) >= abs(observed_value) - 1e-12 for v in date_pool) / len(date_pool),
            })
    primary_outcome = spec["outcomes"][0]
    secondary_outcomes = spec["outcomes"][1:]
    valuation = [row for row in results if row["outcome"] == primary_outcome]
    summary = {
        "status": "exploratory_mechanism_event_study_complete", "experiment_id": spec["experiment_id"],
        "specification_version": spec["document_version"], "freeze_date": spec["freeze_date"],
        "panel_start": panel_start.isoformat(), "panel_end": panel_end.isoformat(),
        "events": len(spec["events"]), "outcomes": spec["outcomes"],
        "pre_window_days": pre, "post_window_days": post,
        "valuation_results": [{k: row[k] for k in ("event_id", "transition", "expected_sign", "difference_in_differences",
                                                    "sign_matches_expectation", "asset_placebo_p_two_sided", "date_placebo_p_two_sided",
                                                    "controls_used", "asset_placebos", "date_placebos")} for row in valuation],
        "primary_outcome": primary_outcome,
        "secondary_outcome_results": [{k: row[k] for k in ("event_id", "outcome", "difference_in_differences", "asset_placebo_p_two_sided",
                                                            "date_placebo_p_two_sided")} for row in results if row["outcome"] in secondary_outcomes],
        "events_with_expected_sign": sum(row["sign_matches_expectation"] for row in valuation),
        "events_rejecting_at_10pct_asset_placebo": sum(row["asset_placebo_p_two_sided"] <= 0.10 for row in valuation),
        "selection_rule": spec["selection_rule"], "interpretation": spec["interpretation"],
        "announcement_caveats": {event["event_id"]: event["announcement_caveat"] for event in spec["events"]},
    }
    return results, summary


def run(repo: Path, spec_path: str = "config/crypto_mechanism_event_study.json") -> dict[str, Any]:
    spec = json.loads((repo / spec_path).read_text(encoding="utf-8"))
    ledger = json.loads((repo / spec["ledger"]).read_text(encoding="utf-8"))
    results, summary = build(spec, ledger, read_csv(repo / spec["panel"]))
    out = repo / "data/processed/02_valuation"
    out.mkdir(parents=True, exist_ok=True)
    stem = spec.get("output_stem", "crypto_mechanism_event_study")
    with (out / f"{stem}.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(results)
    (out / f"{stem}.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Estimate the frozen exploratory mechanism activation event study")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--spec", default="config/crypto_mechanism_event_study.json")
    arguments = parser.parse_args()
    print(json.dumps(run(arguments.repo.resolve(), arguments.spec), indent=2))
