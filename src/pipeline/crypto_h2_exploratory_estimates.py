from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

from src.pipeline.crypto_h2_estimator_diagnostics import (
    CHAIN_COLUMNS,
    POOLED_COLUMNS,
    eligible,
    matrix_rank,
    read_rows,
    two_way_demean,
)


def solve(matrix: list[list[float]], vector: list[float], tolerance: float = 1e-12) -> list[float]:
    size = len(vector)
    augmented = [matrix[row][:] + [vector[row]] for row in range(size)]
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) <= tolerance:
            raise ValueError("singular normal-equation matrix")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        divisor = augmented[column][column]
        augmented[column] = [value / divisor for value in augmented[column]]
        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            augmented[row] = [
                value - factor * pivot_value
                for value, pivot_value in zip(augmented[row], augmented[column])
            ]
    return [augmented[row][-1] for row in range(size)]


def estimate(
    name: str,
    rows: list[dict[str, Any]],
    outcome: str,
    columns: tuple[str, ...],
) -> dict[str, Any]:
    transformed_x = two_way_demean(rows, columns)
    transformed_y = [values[0] for values in two_way_demean(rows, (outcome,))]
    if matrix_rank(transformed_x) != len(columns):
        raise ValueError(f"{name} transformed design is not full rank")

    xtx = [
        [sum(row[left] * row[right] for row in transformed_x) for right in range(len(columns))]
        for left in range(len(columns))
    ]
    xty = [
        sum(row[column] * value for row, value in zip(transformed_x, transformed_y))
        for column in range(len(columns))
    ]
    coefficients = solve(xtx, xty)
    fitted = [sum(value * coefficient for value, coefficient in zip(row, coefficients)) for row in transformed_x]
    residuals = [value - prediction for value, prediction in zip(transformed_y, fitted)]
    tss = sum(value * value for value in transformed_y)
    rss = sum(value * value for value in residuals)
    asset_count = len({row["asset_id"] for row in rows})
    date_count = len({row["date"] for row in rows})
    residual_degrees_of_freedom = len(rows) - len(columns) - (asset_count - 1) - (date_count - 1)
    if residual_degrees_of_freedom <= 0:
        raise ValueError(f"{name} has no residual degrees of freedom")
    return {
        "specification": name,
        "outcome": outcome,
        "rows": len(rows),
        "assets": asset_count,
        "dates": date_count,
        "coefficients": dict(zip(columns, coefficients)),
        "within_r_squared": 1.0 - rss / tss if tss > 0 else None,
        "residual_degrees_of_freedom": residual_degrees_of_freedom,
        "residual_rmse": math.sqrt(rss / residual_degrees_of_freedom),
        "standard_errors": None,
        "p_values": None,
    }


def build(rows: list[dict[str, str]]) -> dict[str, Any]:
    specifications = [
        ("pooled_market_cap", "log_market_cap_usd", None, POOLED_COLUMNS),
        ("pooled_forward_return", "forward_log_return_7d", None, POOLED_COLUMNS),
        ("chain_market_cap", "log_market_cap_usd", "chain", CHAIN_COLUMNS),
        ("chain_forward_return", "forward_log_return_7d", "chain", CHAIN_COLUMNS),
    ]
    estimates = []
    for name, outcome, scope, columns in specifications:
        estimates.append(estimate(name, eligible(rows, outcome, scope), outcome, columns))

    level_rows = eligible(rows, "log_market_cap_usd")
    leave_one_out = []
    for asset_id in sorted({row["asset_id"] for row in level_rows}):
        subset = [row for row in level_rows if row["asset_id"] != asset_id]
        result = estimate(
            f"pooled_market_cap_without_{asset_id}",
            subset,
            "log_market_cap_usd",
            POOLED_COLUMNS,
        )
        leave_one_out.append(
            {
                "excluded_asset": asset_id,
                "rows": result["rows"],
                "fees_x_capture": result["coefficients"]["fees_x_capture"],
                "within_r_squared": result["within_r_squared"],
            }
        )

    return {
        "status": "exploratory_point_estimates_only",
        "estimand": "within-asset and within-date association",
        "estimates": estimates,
        "leave_one_asset_out": leave_one_out,
        "guardrails": [
            f"No standard errors or p-values are reported in this point-estimate artifact; inference is produced separately for the {len({row['asset_id'] for row in rows})}-cluster pilot.",
            "Coefficients are descriptive associations, not causal effects or valuation recommendations.",
            "Chain and application fee scopes are not interchangeable; pooled models retain the predeclared scope interaction.",
            "Overlapping seven-day returns require horizon-robust inference before confirmatory interpretation.",
        ],
    }


def run(repo: Path) -> dict[str, Any]:
    result = build(read_rows(repo / "data/processed/02_valuation/crypto_h2_exploratory_daily.csv"))
    output = repo / "data/processed/02_valuation/crypto_h2_exploratory_estimates.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    coefficient_rows = []
    for estimate_result in result["estimates"]:
        for variable, coefficient in estimate_result["coefficients"].items():
            coefficient_rows.append(
                {
                    "specification": estimate_result["specification"],
                    "outcome": estimate_result["outcome"],
                    "variable": variable,
                    "coefficient": coefficient,
                    "rows": estimate_result["rows"],
                    "assets": estimate_result["assets"],
                    "within_r_squared": estimate_result["within_r_squared"],
                }
            )
    with (output.parent / "crypto_h2_exploratory_estimates.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(coefficient_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(coefficient_rows)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Estimate guarded exploratory H2 fixed-effect models")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()), indent=2))
