from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
from pathlib import Path
from typing import Any


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def slope(x: list[float], y: list[float]) -> float:
    x_mean, y_mean = sum(x) / len(x), sum(y) / len(y)
    denominator = sum((value - x_mean) ** 2 for value in x)
    if denominator == 0:
        raise ValueError("H8 breadth requires cross-asset variation")
    return sum((left - x_mean) * (right - y_mean) for left, right in zip(x, y)) / denominator


def ranks(values: list[float]) -> list[float]:
    ordered = sorted((value, index) for index, value in enumerate(values))
    output = [0.0] * len(values)
    cursor = 0
    while cursor < len(ordered):
        end = cursor
        while end + 1 < len(ordered) and ordered[end + 1][0] == ordered[cursor][0]:
            end += 1
        rank = (cursor + end + 2) / 2
        for _, index in ordered[cursor:end + 1]:
            output[index] = rank
        cursor = end + 1
    return output


def correlation(x: list[float], y: list[float]) -> float:
    x_mean, y_mean = sum(x) / len(x), sum(y) / len(y)
    numerator = sum((left - x_mean) * (right - y_mean) for left, right in zip(x, y))
    denominator = math.sqrt(sum((v - x_mean) ** 2 for v in x) * sum((v - y_mean) ** 2 for v in y))
    return numerator / denominator if denominator else 0.0


def build(readiness: list[dict[str, str]], market: list[dict[str, str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    ready = {
        row["asset_id"]: int(row["h8_value_accrual_breadth"])
        for row in readiness if row["h8_design_ready"] == "1"
    }
    if len(ready) != 5:
        raise ValueError("H8 pilot requires exactly five complete-case assets")
    observations: dict[str, list[float]] = {asset_id: [] for asset_id in ready}
    for row in market:
        if row["asset_id"] in ready and row.get("market_cap_usd"):
            value = float(row["market_cap_usd"])
            if value > 0:
                observations[row["asset_id"]].append(math.log(value))
    if any(not values for values in observations.values()):
        raise ValueError("every H8 asset requires positive market-cap observations")
    rows = [
        {"asset_id": asset_id, "h8_value_accrual_breadth": ready[asset_id],
         "market_cap_days": len(observations[asset_id]),
         "mean_log_market_cap_usd": sum(observations[asset_id]) / len(observations[asset_id])}
        for asset_id in sorted(ready)
    ]
    x = [float(row["h8_value_accrual_breadth"]) for row in rows]
    y = [float(row["mean_log_market_cap_usd"]) for row in rows]
    observed_slope = slope(x, y)
    observed_rank = correlation(ranks(x), ranks(y))
    permutations = list(itertools.permutations(x))
    slope_null = [slope(list(permutation), y) for permutation in permutations]
    rank_null = [correlation(ranks(list(permutation)), ranks(y)) for permutation in permutations]
    loo = []
    for omitted in range(len(rows)):
        loo_x = [value for index, value in enumerate(x) if index != omitted]
        loo_y = [value for index, value in enumerate(y) if index != omitted]
        loo.append({"excluded_asset": rows[omitted]["asset_id"], "slope": slope(loo_x, loo_y)})
    summary = {
        "status": "exploratory_five_asset_h8_complete",
        "assets": len(rows),
        "outcome": "mean_log_market_cap_usd_over_common_h2_window",
        "predictor": "verified_raw_ten_code_value_accrual_breadth",
        "slope": observed_slope,
        "exact_permutation_p_two_sided": sum(abs(value) >= abs(observed_slope) - 1e-12 for value in slope_null) / len(permutations),
        "spearman_rank_correlation": observed_rank,
        "exact_rank_permutation_p_two_sided": sum(abs(value) >= abs(observed_rank) - 1e-12 for value in rank_null) / len(permutations),
        "permutations": len(permutations),
        "leave_one_asset_out": loo,
        "leave_one_asset_out_positive": sum(row["slope"] > 0 for row in loo),
        "guardrails": [
            "Five assets provide only descriptive cross-sectional evidence and very coarse exact inference.",
            "Raw breadth treats every verified function equally; no outcome-tuned weights are estimated.",
            "Breadth may proxy for asset class, age, scale, or ecosystem maturity and is not causal.",
            "BNB remains excluded only because this five-asset pilot was frozen before its classifications were resolved; it must enter a separately versioned extension.",
        ],
    }
    return rows, summary


def run(repo: Path) -> dict[str, Any]:
    preregistration = json.loads((repo / "config/preregistration_h2_h8_pilot.json").read_text(encoding="utf-8"))
    frozen_assets = set(preregistration["H8"]["complete_case_assets"])
    readiness = [row for row in read_csv(repo / "data/processed/01_classification/crypto_h2_h8_pilot_readiness.csv")
                 if row["asset_id"] in frozen_assets]
    rows, summary = build(
        readiness,
        read_csv(repo / "data/processed/02_valuation/crypto_h2_exploratory_daily.csv"),
    )
    output = repo / "data/processed/02_valuation"
    with (output / "crypto_h8_breadth_pilot.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    (output / "crypto_h8_breadth_pilot.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Estimate the five-asset exploratory H8 breadth pilot")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()), indent=2))
