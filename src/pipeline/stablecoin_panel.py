from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from .historical import read_csv, write_rows
from .registry import load_json, validate_asset_config


BANDS_BPS = (10, 25, 50, 100, 500)


def number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def build_panel(assets: list[dict[str, Any]], prices: list[dict[str, Any]], supplies: list[dict[str, Any]], scores: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stable_ids = {asset["asset_id"] for asset in assets if asset["universe"] == "stablecoin" and asset["asset_id"] != "stable_paxg"}
    asset_index = {asset["asset_id"]: asset for asset in assets}
    supply_index = {(row["asset_id"], row["date"]): row for row in supplies}
    score_index = {row["asset_id"]: row for row in scores}
    output: list[dict[str, Any]] = []
    for source in prices:
        asset_id = source["asset_id"]
        if asset_id not in stable_ids:
            continue
        price = number(source.get("price_usd"))
        if price is None or price <= 0:
            continue
        signed = price - 1.0
        absolute = abs(signed)
        supply = supply_index.get((asset_id, source["date"]), {})
        score = score_index.get(asset_id, {})
        score_date = score.get("evidence_date")
        score_is_effective = bool(score_date and source["date"] >= score_date)
        row: dict[str, Any] = {
            "asset_id": asset_id, "date": source["date"], "target_usd": 1.0, "price_usd": price,
            "sample_tier": asset_index[asset_id].get("tier"),
            "failure_control": int(asset_index[asset_id].get("tier") == "failure_control"),
            "signed_deviation": signed, "signed_deviation_bps": signed * 10_000,
            "absolute_peg_error": absolute, "absolute_peg_error_bps": absolute * 10_000,
            "downside_squared_deviation": min(signed, 0.0) ** 2,
            "circulating_peg_usd": number(supply.get("circulating_peg_usd")),
            "price_provider": source.get("provider"), "supply_provider": supply.get("provider"),
            "reserve_quality_score": number(score.get("reserve_quality_score")) if score_is_effective else None,
            "transparency_score": number(score.get("transparency_score")) if score_is_effective else None,
            "redemption_friction_score": number(score.get("redemption_friction_score")) if score_is_effective else None,
            "risk_methodology_version": score.get("methodology_version") if score_is_effective else None,
            "risk_score_evidence_date": score_date if score_is_effective else None,
        }
        for band in BANDS_BPS:
            row[f"breach_{band}bps"] = int(absolute * 10_000 > band)
        output.append(row)
    output.sort(key=lambda row: (row["asset_id"], row["date"]))
    return output


def detect_episodes(rows: list[dict[str, Any]], breach_bps: float = 50, recovery_bps: float = 25) -> list[dict[str, Any]]:
    if recovery_bps >= breach_bps or recovery_bps < 0:
        raise ValueError("recovery_bps must be non-negative and below breach_bps")
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row["asset_id"], []).append(row)
    episodes: list[dict[str, Any]] = []
    for asset_id, asset_rows in sorted(grouped.items()):
        asset_rows.sort(key=lambda row: row["date"])
        active: dict[str, Any] | None = None
        prior_day: date | None = None
        sequence = 0

        def close(censor_reason: str | None, recovery_date: date | None = None) -> None:
            nonlocal active
            assert active is not None
            onset = active["onset"]
            last = active["last"]
            elapsed = (recovery_date - onset).days if recovery_date else (last - onset).days + 1
            episodes.append({
                "episode_id": f"{asset_id}_{int(breach_bps)}bps_{active['sequence']:03d}",
                "asset_id": asset_id, "breach_bps": breach_bps, "recovery_bps": recovery_bps,
                "onset_date": onset.isoformat(), "last_episode_date": last.isoformat(),
                "recovery_date": recovery_date.isoformat() if recovery_date else "",
                "elapsed_days_to_recovery_or_censor": elapsed, "observed_episode_days": active["observations"],
                "maximum_absolute_deviation_bps": active["max_abs_bps"],
                "maximum_discount_bps": active["max_discount_bps"], "maximum_premium_bps": active["max_premium_bps"],
                "area_under_deviation_bps_days": active["aud_bps_days"],
                "failure_control": active["failure_control"],
                "data_review_flag": int(active["max_abs_bps"] > 2_000),
                "recovered": int(recovery_date is not None), "right_censored": int(recovery_date is None),
                "censor_reason": censor_reason or "",
            })
            active = None

        for row in asset_rows:
            day = date.fromisoformat(row["date"])
            if active is not None and prior_day is not None and day > prior_day + timedelta(days=1):
                close("missing_calendar_gap")
            deviation_bps = float(row["signed_deviation_bps"])
            absolute_bps = abs(deviation_bps)
            if active is None and absolute_bps > breach_bps:
                sequence += 1
                active = {
                    "sequence": sequence, "onset": day, "last": day, "observations": 1,
                    "max_abs_bps": absolute_bps, "max_discount_bps": min(deviation_bps, 0.0),
                    "max_premium_bps": max(deviation_bps, 0.0), "aud_bps_days": absolute_bps,
                    "failure_control": int(row.get("failure_control", 0)),
                }
            elif active is not None:
                if absolute_bps <= recovery_bps:
                    close(None, day)
                else:
                    active["last"] = day
                    active["observations"] += 1
                    active["max_abs_bps"] = max(active["max_abs_bps"], absolute_bps)
                    active["max_discount_bps"] = min(active["max_discount_bps"], deviation_bps)
                    active["max_premium_bps"] = max(active["max_premium_bps"], deviation_bps)
                    active["aud_bps_days"] += absolute_bps
            prior_day = day
        if active is not None:
            close("sample_end")
    return episodes


def summarize(panel: list[dict[str, Any]], episodes: list[dict[str, Any]]) -> dict[str, Any]:
    assets = sorted({row["asset_id"] for row in panel})
    return {
        "panel_rows": len(panel), "assets": len(assets), "asset_ids": assets,
        "episodes": len(episodes), "recovered_episodes": sum(row["recovered"] for row in episodes),
        "censored_episodes": sum(row["right_censored"] for row in episodes),
        "primary_sample_episodes_ex_failure_control": sum(not row["failure_control"] for row in episodes),
        "data_review_episodes": sum(row["data_review_flag"] for row in episodes),
        "breach_days_50bps": sum(row["breach_50bps"] for row in panel),
        "primary_sample_breach_days_50bps": sum(row["breach_50bps"] for row in panel if not row["failure_control"]),
        "median_absolute_peg_error_bps": sorted(row["absolute_peg_error_bps"] for row in panel)[len(panel) // 2] if panel else None,
    }


def run(repo: Path, breach_bps: float = 50, recovery_bps: float = 25) -> dict[str, Any]:
    assets = validate_asset_config(load_json(repo / "config" / "assets.json"))
    prices = read_csv(repo / "data" / "processed" / "historical" / "price_daily_defillama.csv")
    supplies = read_csv(repo / "data" / "processed" / "historical" / "stablecoin_supply_daily.csv")
    scores = read_csv(repo / "data" / "processed" / "stablecoin_risk_scores.csv")
    panel = build_panel(assets, prices, supplies, scores)
    episodes = detect_episodes(panel, breach_bps, recovery_bps)
    out = repo / "data" / "processed" / "empirical"
    panel_fields = ["asset_id", "date", "sample_tier", "failure_control", "target_usd", "price_usd", "signed_deviation", "signed_deviation_bps", "absolute_peg_error", "absolute_peg_error_bps", "downside_squared_deviation", *[f"breach_{band}bps" for band in BANDS_BPS], "circulating_peg_usd", "price_provider", "supply_provider", "reserve_quality_score", "transparency_score", "redemption_friction_score", "risk_methodology_version", "risk_score_evidence_date"]
    episode_fields = ["episode_id", "asset_id", "failure_control", "breach_bps", "recovery_bps", "onset_date", "last_episode_date", "recovery_date", "elapsed_days_to_recovery_or_censor", "observed_episode_days", "maximum_absolute_deviation_bps", "maximum_discount_bps", "maximum_premium_bps", "area_under_deviation_bps_days", "recovered", "right_censored", "censor_reason", "data_review_flag"]
    write_rows(out / "stablecoin_daily.csv", panel, panel_fields)
    write_rows(out / "stablecoin_depeg_episodes.csv", episodes, episode_fields)
    summary = summarize(panel, episodes)
    summary.update({"breach_bps": breach_bps, "recovery_bps": recovery_bps, "paxg_excluded_reason": "commodity-referenced target requires gold benchmark"})
    (out / "stablecoin_panel_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    findings = repo / "research" / "findings" / "stablecoin-daily-panel-and-depeg-events.md"
    findings.write_text(f"""# Stablecoin Daily Panel and Depeg Events

- USD-target stablecoins: {summary['assets']} (PAXG excluded because its target is gold, not USD).
- Asset-day observations: {summary['panel_rows']:,}.
- Daily 50-bps breach observations: {summary['breach_days_50bps']:,}.
- Primary episodes: {summary['episodes']} using a {breach_bps:g}-bps onset and {recovery_bps:g}-bps recovery band.
- Primary-model episodes excluding the USTC failure control: {summary['primary_sample_episodes_ex_failure_control']}.
- Recovered episodes: {summary['recovered_episodes']}; right-censored episodes: {summary['censored_episodes']}.
- Extreme-deviation episodes flagged for source review: {summary['data_review_episodes']}.
- Panel median absolute peg error: {summary['median_absolute_peg_error_bps']:.3f} bps.

An episode starts on the first daily observation outside the onset band and remains open until the first observation inside the narrower recovery band. Calendar gaps censor an open episode rather than being silently bridged. Area under deviation sums absolute basis-point deviations over observed episode days. These daily definitions are intended for the long panel; the notebook's consecutive-observation intraday rule remains the primary specification for future five-minute event data.
""", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the USD-stablecoin daily panel and depeg episodes")
    parser.add_argument("--repo", type=Path, default=Path.cwd()); parser.add_argument("--breach-bps", type=float, default=50); parser.add_argument("--recovery-bps", type=float, default=25)
    args = parser.parse_args(); print(json.dumps(run(args.repo.resolve(), args.breach_bps, args.recovery_bps), indent=2))


if __name__ == "__main__": main()
