from __future__ import annotations

import argparse
import itertools
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
from src.pipeline.crypto_h2_exploratory_estimates import solve


TARGET = "fees_x_capture"


def transpose(matrix: list[list[float]]) -> list[list[float]]:
    return [list(column) for column in zip(*matrix)]


def multiply(left: list[list[float]], right: list[list[float]]) -> list[list[float]]:
    return [
        [sum(a * b for a, b in zip(row, column)) for column in transpose(right)]
        for row in left
    ]


def inverse(matrix: list[list[float]]) -> list[list[float]]:
    size = len(matrix)
    inverse_columns = [
        solve(matrix, [float(row == column) for row in range(size)])
        for column in range(size)
    ]
    return transpose(inverse_columns)


def fit(x: list[list[float]], y: list[float]) -> tuple[list[float], list[float], list[float], list[list[float]]]:
    if matrix_rank(x) != len(x[0]):
        raise ValueError("transformed design is not full rank")
    xt = transpose(x)
    xtx = multiply(xt, x)
    xty = [sum(value * outcome for value, outcome in zip(column, y)) for column in xt]
    coefficients = solve(xtx, xty)
    fitted = [sum(value * coefficient for value, coefficient in zip(row, coefficients)) for row in x]
    residuals = [outcome - prediction for outcome, prediction in zip(y, fitted)]
    return coefficients, fitted, residuals, inverse(xtx)


def cluster_standard_errors(
    x: list[list[float]],
    residuals: list[float],
    cluster_ids: list[str],
    xtx_inverse: list[list[float]],
) -> list[float]:
    clusters = sorted(set(cluster_ids))
    observations, regressors, cluster_count = len(x), len(x[0]), len(clusters)
    if cluster_count <= 1 or observations <= regressors:
        raise ValueError("cluster covariance requires multiple clusters and residual degrees of freedom")
    meat = [[0.0 for _ in range(regressors)] for _ in range(regressors)]
    for cluster in clusters:
        score = [
            sum(row[column] * residual for row, residual, label in zip(x, residuals, cluster_ids) if label == cluster)
            for column in range(regressors)
        ]
        for left in range(regressors):
            for right in range(regressors):
                meat[left][right] += score[left] * score[right]
    correction = (cluster_count / (cluster_count - 1)) * ((observations - 1) / (observations - regressors))
    covariance = multiply(multiply(xtx_inverse, meat), xtx_inverse)
    return [math.sqrt(max(0.0, correction * covariance[index][index])) for index in range(regressors)]


def wild_cluster_test(
    rows: list[dict[str, Any]],
    outcome: str,
    columns: tuple[str, ...],
    target: str = TARGET,
) -> dict[str, Any]:
    x = two_way_demean(rows, columns)
    y = [values[0] for values in two_way_demean(rows, (outcome,))]
    clusters = [row["asset_id"] for row in rows]
    labels = sorted(set(clusters))
    target_index = columns.index(target)

    coefficients, _, residuals, xtx_inverse = fit(x, y)
    standard_errors = cluster_standard_errors(x, residuals, clusters, xtx_inverse)
    observed_t = coefficients[target_index] / standard_errors[target_index]

    restricted_x = [[row[index] for index, column in enumerate(columns) if column != target] for row in x]
    _, restricted_fitted, restricted_residuals, _ = fit(restricted_x, y)

    bootstrap_t = []
    for signs in itertools.product((-1.0, 1.0), repeat=len(labels)):
        weights = dict(zip(labels, signs))
        bootstrap_y = [
            fitted + weights[cluster] * residual
            for fitted, residual, cluster in zip(restricted_fitted, restricted_residuals, clusters)
        ]
        bootstrap_coefficients, _, bootstrap_residuals, bootstrap_inverse = fit(x, bootstrap_y)
        bootstrap_se = cluster_standard_errors(x, bootstrap_residuals, clusters, bootstrap_inverse)
        bootstrap_t.append(bootstrap_coefficients[target_index] / bootstrap_se[target_index])

    exceedances = sum(abs(value) >= abs(observed_t) - 1e-12 for value in bootstrap_t)
    return {
        "coefficient": coefficients[target_index],
        "cluster_robust_standard_error_cr1": standard_errors[target_index],
        "observed_t": observed_t,
        "wild_cluster_bootstrap_p_two_sided": exceedances / len(bootstrap_t),
        "bootstrap_assignments": len(bootstrap_t),
        "clusters": len(labels),
        "minimum_two_sided_p_resolution": 2 / len(bootstrap_t),
    }


def build(rows: list[dict[str, str]]) -> dict[str, Any]:
    specifications = [
        ("pooled_market_cap", "log_market_cap_usd", None, POOLED_COLUMNS),
        ("pooled_forward_return", "forward_log_return_7d", None, POOLED_COLUMNS),
        ("chain_market_cap", "log_market_cap_usd", "chain", CHAIN_COLUMNS),
        ("chain_forward_return", "forward_log_return_7d", "chain", CHAIN_COLUMNS),
    ]
    results = []
    for name, outcome, scope, columns in specifications:
        result = wild_cluster_test(eligible(rows, outcome, scope), outcome, columns)
        result.update(
            {
                "specification": name,
                "outcome": outcome,
                "overlapping_outcome": outcome == "forward_log_return_7d",
            }
        )
        results.append(result)
    return {
        "status": "exploratory_small_cluster_inference_complete",
        "null_hypothesis": "fees_x_capture = 0",
        "method": "CR1 asset-clustered t statistic with exhaustive Rademacher wild-cluster bootstrap under the null",
        "results": results,
        "guardrails": [
            "Bootstrap assignments are enumerated exactly; p-value resolution is coarse with four or six clusters.",
            "Forward-return results remain non-confirmatory because overlapping seven-day outcomes require horizon-robust treatment.",
            "The pilot was not frozen before these estimates were observed, so all inference remains exploratory.",
            "Statistical association does not establish causality or investment value.",
        ],
    }


def run(repo: Path) -> dict[str, Any]:
    result = build(read_rows(repo / "data/processed/empirical/crypto_h2_exploratory_daily.csv"))
    output = repo / "data/processed/empirical/crypto_h2_small_cluster_inference.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run exhaustive exploratory H2 wild-cluster inference")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()), indent=2))
