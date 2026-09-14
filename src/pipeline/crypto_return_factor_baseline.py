from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from .crypto_h2_exploratory_estimates import solve
from .crypto_h8_breadth_pilot import read_csv


def validate(spec: dict[str, Any]) -> None:
    if spec.get("schema_version") != 1 or spec.get("status") != "frozen_before_baseline_estimation":
        raise ValueError("unsupported return factor baseline specification")
    if not spec.get("fama_macbeth", {}).get("predictors") or not spec.get("function_sorts", {}).get("bundles"):
        raise ValueError("baseline requires listed predictors and sort bundles")


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


def newey_west_t(series: list[float], lags: int) -> tuple[float, float, float]:
    n = len(series)
    mean = statistics.fmean(series)
    centered = [v - mean for v in series]
    variance = sum(v * v for v in centered) / n
    for lag in range(1, lags + 1):
        weight = 1 - lag / (lags + 1)
        cov = sum(centered[i] * centered[i - lag] for i in range(lag, n)) / n
        variance += 2 * weight * cov
    se = math.sqrt(max(variance, 0.0) / n)
    return mean, se, (mean / se if se > 0 else float("nan"))


def market_models(rows: list[dict[str, Any]], factor: str, minimum: int) -> list[dict[str, Any]]:
    by_asset: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for row in rows:
        r, m = number(row["log_return"]), number(row[factor])
        if r is not None and m is not None:
            by_asset[row["asset_id"]].append((m, r))
    output = []
    for asset in sorted(by_asset):
        pairs = by_asset[asset]
        if len(pairs) < minimum:
            output.append({"asset_id": asset, "days": len(pairs), "status": "insufficient_history"})
            continue
        x, y = [p[0] for p in pairs], [p[1] for p in pairs]
        coefficients = ols([[v] for v in x], y)
        if coefficients is None:
            output.append({"asset_id": asset, "days": len(pairs), "status": "not_estimable"})
            continue
        alpha, b = coefficients
        fitted = [alpha + b * v for v in x]
        ss_res = sum((yi - fi) ** 2 for yi, fi in zip(y, fitted))
        ss_tot = sum((yi - statistics.fmean(y)) ** 2 for yi in y)
        output.append({"asset_id": asset, "days": len(pairs), "status": "estimated", "market_beta": b,
                       "alpha_daily": alpha, "alpha_annualized": alpha * 365,
                       "r_squared": 1 - ss_res / ss_tot if ss_tot else None,
                       "mean_log_return_annualized": statistics.fmean(y) * 365,
                       "volatility_annualized": statistics.pstdev(y) * math.sqrt(365)})
    return output


def fama_macbeth(rows: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    predictors = config["predictors"]
    by_asset: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        by_asset[row["asset_id"]][row["date"]] = row
    dates = sorted({row["date"] for row in rows})
    previous = {d: dates[i - 1] for i, d in enumerate(dates) if i > 0}
    daily: list[list[float]] = []
    used_dates = 0
    for day in dates:
        if day not in previous:
            continue
        x, y = [], []
        for asset, series in by_asset.items():
            current = series.get(day)
            lagged = series.get(previous[day]) if config["lag_predictors_one_day"] else current
            if current is None or lagged is None:
                continue
            r = number(current[config["outcome"]])
            values = [number(lagged[p]) for p in predictors]
            if r is None or any(v is None for v in values):
                continue
            x.append(values); y.append(r)
        if len(y) < config["minimum_assets_per_day"]:
            continue
        coefficients = ols(x, y)
        if coefficients is None:
            continue
        daily.append(coefficients)
        used_dates += 1
    if not daily:
        raise ValueError("Fama-MacBeth requires at least one estimable cross-section")
    results = {}
    for index, name in enumerate(["intercept", *predictors]):
        series = [c[index] for c in daily]
        mean, se, t = newey_west_t(series, config["newey_west_lags"])
        results[name] = {"mean_daily_premium": mean, "newey_west_se": se, "t_statistic": t, "share_positive_days": sum(v > 0 for v in series) / len(series)}
    return {"cross_sections": used_dates, "predictors": predictors, "results": results}


def max_drawdown(log_returns: list[float]) -> float:
    peak, level, worst = 0.0, 0.0, 0.0
    for r in log_returns:
        level += r
        peak = max(peak, level)
        worst = min(worst, level - peak)
    return worst


def portfolio_stats(returns: list[float], market: list[float], lags: int) -> dict[str, Any]:
    b = ols([[m] for m in market], returns)
    mean, se, t = newey_west_t(returns, lags)
    return {"days": len(returns), "mean_log_return_annualized": mean * 365, "volatility_annualized": statistics.pstdev(returns) * math.sqrt(365),
            "sharpe_annualized": (mean / statistics.pstdev(returns)) * math.sqrt(365) if statistics.pstdev(returns) else None,
            "market_beta": b[1] if b else None, "max_drawdown_log": max_drawdown(returns), "newey_west_t_of_mean": t}


def function_sorts(rows: list[dict[str, Any]], profiles: list[dict[str, str]], config: dict[str, Any]) -> dict[str, Any]:
    assets = config["assets"]
    profile_index = {p["asset_id"]: p for p in profiles if p["asset_id"] in assets}
    if set(profile_index) != set(assets):
        raise ValueError("function sorts require a Phase 1 profile for every listed asset")
    by_date: dict[str, dict[str, float]] = defaultdict(dict)
    market: dict[str, float] = {}
    for row in rows:
        if row["asset_id"] in assets:
            r = number(row["log_return"])
            if r is not None:
                by_date[row["date"]][row["asset_id"]] = r
                market[row["date"]] = number(row["market_ew_log_return"])
    common = sorted(d for d, v in by_date.items() if len(v) == len(assets))
    if not common:
        raise ValueError("function sorts require a common window across listed assets")
    sorts = []
    for bundle in config["bundles"]:
        positives = [a for a in assets if profile_index[a][bundle] == "1"]
        negatives = [a for a in assets if profile_index[a][bundle] == "0"]
        if not positives or not negatives:
            sorts.append({"bundle": bundle, "status": "no_variation", "positive_assets": positives})
            continue
        long_r = [statistics.fmean(by_date[d][a] for a in positives) for d in common]
        short_r = [statistics.fmean(by_date[d][a] for a in negatives) for d in common]
        mkt = [market[d] for d in common]
        spread = [l - s for l, s in zip(long_r, short_r)]
        sorts.append({"bundle": bundle, "status": "descriptive", "positive_assets": positives, "negative_assets": negatives,
                      "positive_portfolio": portfolio_stats(long_r, mkt, config["newey_west_lags"]),
                      "negative_portfolio": portfolio_stats(short_r, mkt, config["newey_west_lags"]),
                      "long_minus_short": portfolio_stats(spread, mkt, config["newey_west_lags"])})
    return {"common_window_start": common[0], "common_window_end": common[-1], "common_days": len(common), "sorts": sorts}


def build(spec: dict[str, Any], rows: list[dict[str, str]], profiles: list[dict[str, str]]) -> dict[str, Any]:
    validate(spec)
    models = market_models(rows, spec["market_model"]["factor"], spec["market_model"]["minimum_days"])
    estimated = [m for m in models if m["status"] == "estimated"]
    return {
        "status": "return_factor_baseline_complete", "specification_version": spec["document_version"], "freeze_date": spec["freeze_date"],
        "market_model": {"factor": spec["market_model"]["factor"], "assets_estimated": len(estimated),
                          "median_market_beta": statistics.median(m["market_beta"] for m in estimated) if estimated else None,
                          "median_r_squared": statistics.median(m["r_squared"] for m in estimated) if estimated else None,
                          "per_asset": models},
        "fama_macbeth": fama_macbeth(rows, spec["fama_macbeth"]),
        "function_sorts": function_sorts(rows, profiles, spec["function_sorts"]),
        "selection_rule": spec["selection_rule"], "interpretation": spec["interpretation"],
    }


def run(repo: Path) -> dict[str, Any]:
    spec = json.loads((repo / "config/crypto_return_factor_baseline.json").read_text(encoding="utf-8"))
    summary = build(spec, read_csv(repo / spec["panel"]), read_csv(repo / spec["profiles"]))
    out = repo / "data/processed/03_risk"
    (out / "crypto_return_factor_baseline.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    with (out / "crypto_return_market_models.csv").open("w", newline="", encoding="utf-8") as handle:
        rows = summary["market_model"]["per_asset"]
        fields = sorted({k for r in rows for k in r}, key=lambda k: (k != "asset_id", k))
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Estimate the frozen crypto return factor baseline and descriptive function sorts")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()), indent=2))
