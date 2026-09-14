from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from .crypto_h2_exploratory_estimates import solve
from .crypto_h8_breadth_pilot import read_csv


def validate(spec: dict[str, Any]) -> None:
    if spec.get("schema_version") != 1 or spec.get("status") != "frozen_before_risk_estimation":
        raise ValueError("unsupported function risk exposure specification")
    if not spec.get("predictors") or not spec.get("outcomes") or not spec.get("samples"):
        raise ValueError("risk exposure test requires predictors, outcomes, and samples")
    if not spec.get("selection_rule") or not spec.get("interpretation"):
        raise ValueError("risk exposure test requires selection and interpretation guardrails")
    for sample in spec["samples"]:
        if sample.get("inference") not in {"exact_permutation", "monte_carlo_permutation"}:
            raise ValueError(f"sample {sample.get('id')} has an unsupported inference mode")


def number(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def ols(x: list[list[float]], y: list[float]) -> list[float] | None:
    design = [[1.0, *row] for row in x]
    k = len(design[0])
    if len(design) <= k:
        return None
    xtx = [[sum(r[i] * r[j] for r in design) for j in range(k)] for i in range(k)]
    xty = [sum(r[i] * v for r, v in zip(design, y)) for i in range(k)]
    try:
        return solve(xtx, xty)
    except (ValueError, ZeroDivisionError):
        return None


def max_drawdown(returns: list[float]) -> float:
    peak = level = worst = 0.0
    for value in returns:
        level += value
        peak = max(peak, level)
        worst = min(worst, level - peak)
    return worst


def risk_metrics(rows: list[dict[str, str]], window: dict[str, Any]) -> dict[str, dict[str, float]]:
    start, end = window["start"], window["end"]
    series: dict[str, list[tuple[str, float, float | None, float | None]]] = defaultdict(list)
    for row in rows:
        if not start <= row["date"] <= end:
            continue
        asset_return, market = number(row["log_return"]), number(row["market_ew_log_return"])
        if asset_return is None or market is None:
            continue
        series[row["asset_id"]].append((row["date"], asset_return, market, number(row["log_dollar_volume"])))
    minimum = window["minimum_coverage_share"] * window["expected_days"]
    metrics: dict[str, dict[str, float]] = {}
    for asset, observations in series.items():
        if len(observations) < minimum:
            continue
        observations.sort()
        returns = [value for _, value, _, _ in observations]
        market = [value for _, _, value, _ in observations]
        volumes = [value for _, _, _, value in observations if value is not None]
        coefficients = ols([[value] for value in market], returns)
        if coefficients is None or not volumes:
            continue
        metrics[asset] = {
            "days": len(observations),
            "market_beta": coefficients[1],
            "realized_volatility_annualized": statistics.pstdev(returns) * math.sqrt(365),
            "max_drawdown_log": max_drawdown(returns),
            "mean_log_dollar_volume": statistics.fmean(volumes),
        }
    return metrics


def verified_features(profiles: list[dict[str, str]], predictors: list[str]) -> dict[str, dict[str, float]]:
    features = {}
    for row in profiles:
        if row.get("classification_status") != "complete_verified":
            continue
        features[row["asset_id"]] = {name: float(row[name]) for name in predictors}
    return features


def provisional_features(design: dict[str, Any], bundle_spec: dict[str, Any], predictors: list[str]) -> dict[str, dict[str, float]]:
    order = design["value_accrual_codes"]
    bundles = bundle_spec["bundles"]
    features = {}
    for asset in design["assets"]:
        codes = dict(zip(order, asset["codes"]))
        row: dict[str, float] = {}
        for name in predictors:
            if name == "raw_function_breadth":
                row[name] = float(sum(codes.values()))
            else:
                members = bundles[name.removeprefix("bundle_")]
                row[name] = float(any(codes[code] for code in members))
        features[asset["asset_id"]] = row
    return features


def benjamini_hochberg(p_values: list[float]) -> list[float]:
    indexed = sorted(range(len(p_values)), key=lambda i: p_values[i])
    total = len(p_values)
    q = [0.0] * total
    running = 1.0
    for rank in range(total - 1, -1, -1):
        index = indexed[rank]
        running = min(running, p_values[index] * total / (rank + 1))
        q[index] = min(1.0, running)
    return q


def test_predictor(values: list[float], outcome: list[float], control: list[float],
                   mode: str, draws: int, rng: random.Random) -> dict[str, Any]:
    if len({round(value, 12) for value in values}) < 2:
        return {"estimable": 0}
    observed = ols([[v, c] for v, c in zip(values, control)], outcome)
    if observed is None:
        return {"estimable": 0}
    coefficient = observed[1]
    exceed = total = 0
    if mode == "exact_permutation":
        for permutation in itertools.permutations(values):
            fit = ols([[v, c] for v, c in zip(permutation, control)], outcome)
            if fit is None:
                continue
            total += 1
            exceed += abs(fit[1]) >= abs(coefficient) - 1e-12
    else:
        shuffled = list(values)
        for _ in range(draws):
            rng.shuffle(shuffled)
            fit = ols([[v, c] for v, c in zip(shuffled, control)], outcome)
            if fit is None:
                continue
            total += 1
            exceed += abs(fit[1]) >= abs(coefficient) - 1e-12
    loo = []
    for omitted in range(len(outcome)):
        fit = ols([[v, c] for i, (v, c) in enumerate(zip(values, control)) if i != omitted],
                  [v for i, v in enumerate(outcome) if i != omitted])
        if fit is not None:
            loo.append(fit[1])
    return {"estimable": 1, "coefficient": coefficient, "size_control_coefficient": observed[2],
            "permutation_p_two_sided": exceed / total if total else None, "permutation_assignments": total,
            "leave_one_out_same_sign": sum((value > 0) == (coefficient > 0) for value in loo), "leave_one_out_samples": len(loo)}


def build(spec: dict[str, Any], panel: list[dict[str, str]], profiles: list[dict[str, str]],
          design: dict[str, Any], bundle_spec: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    validate(spec)
    metrics = risk_metrics(panel, spec["window"])
    if not metrics:
        raise ValueError("risk exposure test requires assets meeting the window coverage rule")
    sources = {"verified_profiles": verified_features(profiles, spec["predictors"]),
               "provisional_design": provisional_features(design, bundle_spec, spec["predictors"])}
    asset_rows: list[dict[str, Any]] = []
    result_rows: list[dict[str, Any]] = []
    sample_summaries = []
    for sample in spec["samples"]:
        features = sources[sample["source"]]
        assets = sorted(set(features) & set(metrics))
        if len(assets) < 4:
            raise ValueError(f"sample {sample['id']} has too few assets to estimate")
        rng = random.Random(spec["inference"]["random_seed"])
        control = [metrics[a]["mean_log_dollar_volume"] for a in assets]
        for asset in assets:
            asset_rows.append({"sample": sample["id"], "asset_id": asset, "evidence_status": sample["evidence_status"],
                               **{k: metrics[asset][k] for k in ("days", "market_beta", "realized_volatility_annualized",
                                                                 "max_drawdown_log", "mean_log_dollar_volume")},
                               **{name: features[asset][name] for name in spec["predictors"]}})
        pending: list[dict[str, Any]] = []
        for outcome_name in spec["outcomes"]:
            outcome = [metrics[a][outcome_name] for a in assets]
            for predictor in spec["predictors"]:
                values = [features[a][predictor] for a in assets]
                result = test_predictor(values, outcome, control, sample["inference"],
                                        spec["inference"]["monte_carlo_draws"], rng)
                pending.append({"sample": sample["id"], "evidence_status": sample["evidence_status"], "assets": len(assets),
                                "outcome": outcome_name, "predictor": predictor, "inference": sample["inference"], **result})
        estimable = [row for row in pending if row["estimable"]]
        q_values = benjamini_hochberg([row["permutation_p_two_sided"] for row in estimable])
        for row, q in zip(estimable, q_values):
            row["benjamini_hochberg_q"] = q
        result_rows.extend(pending)
        significant = [row for row in estimable if row["permutation_p_two_sided"] <= 0.05]
        sample_summaries.append({
            "sample": sample["id"], "evidence_status": sample["evidence_status"], "assets": len(assets),
            "asset_ids": assets, "tests": len(pending), "estimable_tests": len(estimable),
            "unestimable_predictors": sorted({row["predictor"] for row in pending if not row["estimable"]}),
            "tests_p_at_or_below_5pct": len(significant),
            "tests_surviving_fdr_10pct": sum(row["benjamini_hochberg_q"] <= 0.10 for row in estimable),
            "expected_false_positives_at_5pct": round(0.05 * len(estimable), 2),
            "strongest_associations": [
                {k: row[k] for k in ("outcome", "predictor", "coefficient", "permutation_p_two_sided",
                                      "benjamini_hochberg_q", "leave_one_out_same_sign", "leave_one_out_samples")}
                for row in sorted(estimable, key=lambda item: item["permutation_p_two_sided"])[:5]],
        })
    summary = {
        "status": "exploratory_function_risk_exposure_complete", "experiment_id": spec["experiment_id"],
        "specification_version": spec["document_version"], "freeze_date": spec["freeze_date"],
        "window": {k: spec["window"][k] for k in ("start", "end", "expected_days", "minimum_coverage_share")},
        "outcomes": list(spec["outcomes"]), "predictors": spec["predictors"], "control": spec["control"],
        "samples": sample_summaries, "multiple_testing": spec["inference"]["multiple_testing"],
        "selection_rule": spec["selection_rule"], "interpretation": spec["interpretation"],
    }
    return asset_rows, result_rows, summary


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = sorted({key for row in rows for key in row}, key=lambda key: (key not in ("sample", "asset_id", "outcome", "predictor"), key))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", restval="")
        writer.writeheader()
        writer.writerows(rows)


def run(repo: Path) -> dict[str, Any]:
    spec = json.loads((repo / "config/crypto_function_risk_exposure.json").read_text(encoding="utf-8"))
    asset_rows, result_rows, summary = build(
        spec, read_csv(repo / spec["panel"]), read_csv(repo / spec["verified_profiles"]),
        json.loads((repo / spec["provisional_design"]).read_text(encoding="utf-8")),
        json.loads((repo / spec["bundle_map"]).read_text(encoding="utf-8")))
    out = repo / "data/processed/03_risk"
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "crypto_function_risk_assets.csv", asset_rows)
    write_csv(out / "crypto_function_risk_tests.csv", result_rows)
    (out / "crypto_function_risk_exposure.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Estimate the frozen P1_H6 function-versus-risk-exposure test")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()), indent=2))
