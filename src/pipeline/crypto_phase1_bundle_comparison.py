from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
from pathlib import Path
from typing import Any

from .crypto_h2_exploratory_estimates import solve
from .crypto_h8_breadth_pilot import correlation, ranks, read_csv


def validate(spec: dict[str, Any]) -> None:
    if spec.get("schema_version") != 1 or spec.get("status") != "frozen_before_comparison_estimation":
        raise ValueError("unsupported Phase 1 bundle comparison specification")
    if len(spec.get("assets", [])) != 6 or len(set(spec["assets"])) != 6:
        raise ValueError("bundle comparison requires the frozen six-asset core")
    ids = [model["id"] for model in spec.get("models", [])]
    if len(ids) != len(set(ids)) or not ids:
        raise ValueError("model identifiers must be unique and non-empty")
    pair = spec.get("nested_pair", {})
    if pair.get("restricted") not in ids or pair.get("extended") not in ids:
        raise ValueError("nested pair must reference listed models")
    if not spec.get("selection_rule") or not spec.get("interpretation"):
        raise ValueError("bundle comparison requires selection and interpretation guardrails")


def ols(x: list[list[float]], y: list[float]) -> list[float] | None:
    design = [[1.0, *row] for row in x]
    columns = len(design[0])
    xtx = [[sum(r[i] * r[j] for r in design) for j in range(columns)] for i in range(columns)]
    xty = [sum(r[i] * v for r, v in zip(design, y)) for i in range(columns)]
    try:
        return solve(xtx, xty)
    except (ValueError, ZeroDivisionError):
        return None


def predict(coefficients: list[float], row: list[float]) -> float:
    return coefficients[0] + sum(c * v for c, v in zip(coefficients[1:], row))


def loo_rmse(x: list[list[float]], y: list[float]) -> float | None:
    errors = []
    for omitted in range(len(y)):
        train_x = [r for i, r in enumerate(x) if i != omitted]
        train_y = [v for i, v in enumerate(y) if i != omitted]
        coefficients = ols(train_x, train_y)
        if coefficients is None:
            return None
        errors.append((predict(coefficients, x[omitted]) - y[omitted]) ** 2)
    return math.sqrt(sum(errors) / len(errors))


def outcomes_by_asset(rows: list[dict[str, str]], assets: set[str]) -> dict[str, dict[str, float]]:
    cap: dict[str, list[float]] = {a: [] for a in assets}
    multiple: dict[str, list[float]] = {a: [] for a in assets}
    for row in rows:
        asset = row["asset_id"]
        if asset not in assets or not row.get("market_cap_usd"):
            continue
        value = float(row["market_cap_usd"])
        if value <= 0:
            continue
        cap[asset].append(math.log(value))
        fees = row.get("fees_usd_lag1")
        if fees not in ("", None) and float(fees) > 0:
            multiple[asset].append(math.log(value / float(fees)))
    if any(not cap[a] or not multiple[a] for a in assets):
        raise ValueError("every bundle comparison asset requires market-cap and positive fee observations")
    return {a: {"mean_log_market_cap_usd": sum(cap[a]) / len(cap[a]),
                "mean_log_market_cap_to_daily_fees": sum(multiple[a]) / len(multiple[a]),
                "market_cap_days": len(cap[a]), "fee_days": len(multiple[a])} for a in assets}


def build(spec: dict[str, Any], profiles: list[dict[str, str]], panel: list[dict[str, str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    validate(spec)
    assets = set(spec["assets"])
    profile_index = {row["asset_id"]: row for row in profiles if row["asset_id"] in assets}
    if set(profile_index) != assets or any(row["classification_status"] != "complete_verified" for row in profile_index.values()):
        raise ValueError("every bundle comparison asset must have a complete verified Phase 1 profile")
    outcomes = outcomes_by_asset(panel, assets)
    order = sorted(assets)
    rows: list[dict[str, Any]] = []
    best: dict[str, tuple[str, float]] = {}
    for outcome_name in spec["outcomes"]:
        y = [outcomes[a][outcome_name] for a in order]
        for model in spec["models"]:
            x = [[float(profile_index[a][p]) for p in model["predictors"]] for a in order]
            estimable = all(len({r[i] for r in x}) > 1 for i in range(len(model["predictors"])))
            record: dict[str, Any] = {"outcome": outcome_name, "model_id": model["id"], "role": model["role"],
                                      "predictors": "|".join(model["predictors"]), "estimable": int(estimable)}
            if estimable:
                coefficients = ols(x, y)
                rmse = loo_rmse(x, y)
                record.update({"intercept": coefficients[0] if coefficients else None,
                               "slopes": "|".join(f"{c:.6f}" for c in coefficients[1:]) if coefficients else "",
                               "leave_one_out_rmse": rmse})
                if len(model["predictors"]) == 1:
                    single = [r[0] for r in x]
                    observed = correlation(ranks(single), ranks(y))
                    null = [correlation(ranks(list(p)), ranks(y)) for p in itertools.permutations(single)]
                    record.update({"spearman_rank_correlation": observed,
                                   "exact_rank_permutation_p_two_sided": sum(abs(v) >= abs(observed) - 1e-12 for v in null) / len(null)})
                if rmse is not None and (outcome_name not in best or rmse < best[outcome_name][1]):
                    best[outcome_name] = (model["id"], rmse)
            rows.append(record)
    index = {(r["outcome"], r["model_id"]): r for r in rows}
    pair = spec["nested_pair"]
    comparison = []
    for outcome_name in spec["outcomes"]:
        breadth = index[(outcome_name, "raw_breadth")]
        bundles = index[(outcome_name, "active_bundle_count")]
        restricted = index[(outcome_name, pair["restricted"])]
        extended = index[(outcome_name, pair["extended"])]
        comparison.append({
            "outcome": outcome_name,
            "raw_breadth_loo_rmse": breadth.get("leave_one_out_rmse"),
            "active_bundle_count_loo_rmse": bundles.get("leave_one_out_rmse"),
            "bundle_count_beats_raw_breadth": (bundles.get("leave_one_out_rmse") is not None and breadth.get("leave_one_out_rmse") is not None
                                               and bundles["leave_one_out_rmse"] < breadth["leave_one_out_rmse"]),
            "nested_restricted_loo_rmse": restricted.get("leave_one_out_rmse"),
            "nested_extended_loo_rmse": extended.get("leave_one_out_rmse"),
            "theory_addition_improves_out_of_sample": (extended.get("leave_one_out_rmse") is not None and restricted.get("leave_one_out_rmse") is not None
                                                       and extended["leave_one_out_rmse"] < restricted["leave_one_out_rmse"]),
            "best_model_by_loo_rmse": best.get(outcome_name, (None, None))[0],
        })
    breadth_values = [int(profile_index[a]["raw_function_breadth"]) for a in order]
    bundle_values = [int(profile_index[a]["active_bundle_count"]) for a in order]
    summary = {
        "status": "exploratory_bundle_comparison_complete", "experiment_id": spec["experiment_id"],
        "specification_version": spec["document_version"], "freeze_date": spec["freeze_date"],
        "assets": order, "outcomes": list(spec["outcomes"]), "withheld_outcomes": spec["withheld_outcomes"],
        "models": len(spec["models"]), "unestimable_models": sorted({r["model_id"] for r in rows if not r["estimable"]}),
        "raw_breadth_by_asset": dict(zip(order, breadth_values)), "active_bundle_count_by_asset": dict(zip(order, bundle_values)),
        "breadth_bundle_rank_correlation": correlation(ranks([float(v) for v in breadth_values]), ranks([float(v) for v in bundle_values])),
        "comparison": comparison, "comparison_metric": spec["comparison_metric"],
        "selection_rule": spec["selection_rule"], "interpretation": spec["interpretation"],
    }
    return rows, summary


def run(repo: Path) -> dict[str, Any]:
    spec = json.loads((repo / "config/crypto_phase1_bundle_comparison.json").read_text(encoding="utf-8"))
    rows, summary = build(spec, read_csv(repo / spec["profiles"]), read_csv(repo / spec["panel"]))
    out = repo / "data/processed/empirical"
    out.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({k for r in rows for k in r}, key=lambda k: (k not in ("outcome", "model_id", "role", "predictors", "estimable"), k))
    with (out / "crypto_phase1_bundle_comparison.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    (out / "crypto_phase1_bundle_comparison.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Estimate the frozen Phase 1 bundle-versus-breadth comparison")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()), indent=2))
