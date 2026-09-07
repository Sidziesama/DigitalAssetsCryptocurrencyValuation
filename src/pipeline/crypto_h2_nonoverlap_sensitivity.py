from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

from src.pipeline.crypto_h2_estimator_diagnostics import CHAIN_COLUMNS, POOLED_COLUMNS, eligible, read_rows
from src.pipeline.crypto_h2_small_cluster_inference import wild_cluster_test


OUTCOME = "forward_log_return_7d"


def partition_offsets(rows: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    ordinals = {row["date"]: date.fromisoformat(row["date"]).toordinal() for row in rows}
    anchor = min(ordinals.values())
    return {
        offset: [row for row in rows if (ordinals[row["date"]] - anchor) % 7 == offset]
        for offset in range(7)
    }


def assert_nonoverlap(rows: list[dict[str, Any]]) -> None:
    dates = sorted({date.fromisoformat(row["date"]) for row in rows})
    if any((later - earlier).days < 7 for earlier, later in zip(dates, dates[1:])):
        raise ValueError("seven-day forward-return windows overlap")


def build(rows: list[dict[str, str]]) -> dict[str, Any]:
    specifications = [
        ("pooled", None, POOLED_COLUMNS),
        ("chain", "chain", CHAIN_COLUMNS),
    ]
    results = []
    for scope_name, scope, columns in specifications:
        candidate = eligible(rows, OUTCOME, scope)
        partitions = partition_offsets(candidate)
        for offset, subset in partitions.items():
            assert_nonoverlap(subset)
            estimate = wild_cluster_test(subset, OUTCOME, columns)
            estimate.update(
                {
                    "scope": scope_name,
                    "calendar_offset": offset,
                    "rows": len(subset),
                    "dates": len({row["date"] for row in subset}),
                    "first_date": min(row["date"] for row in subset),
                    "last_date": max(row["date"] for row in subset),
                }
            )
            results.append(estimate)

    scope_summaries = []
    for scope_name, _, _ in specifications:
        scope_results = [row for row in results if row["scope"] == scope_name]
        coefficients = [row["coefficient"] for row in scope_results]
        p_values = [row["wild_cluster_bootstrap_p_two_sided"] for row in scope_results]
        scope_summaries.append(
            {
                "scope": scope_name,
                "offsets": len(scope_results),
                "positive_offsets": sum(value > 0 for value in coefficients),
                "negative_offsets": sum(value < 0 for value in coefficients),
                "minimum_coefficient": min(coefficients),
                "maximum_coefficient": max(coefficients),
                "minimum_wild_cluster_p": min(p_values),
                "maximum_wild_cluster_p": max(p_values),
                "offsets_rejecting_at_10pct": sum(value < 0.10 for value in p_values),
            }
        )
    return {
        "status": "nonoverlapping_forward_return_sensitivity_complete",
        "outcome": OUTCOME,
        "window_rule": "For each of seven calendar offsets, retain dates exactly seven days apart so adjacent forward-return intervals do not overlap.",
        "results": results,
        "scope_summaries": scope_summaries,
        "guardrails": [
            "Calendar-offset estimates use roughly one seventh of the already short pilot window.",
            "The seven offsets are sensitivity samples, not seven independent hypothesis tests.",
            "Wild-cluster assignments are enumerated exactly for the pooled and chain samples; finite-cluster p-value resolution is retained in every offset result.",
            "Results remain exploratory because this sensitivity was implemented after inspecting the full-sample pilot estimates.",
        ],
    }


def run(repo: Path) -> dict[str, Any]:
    result = build(read_rows(repo / "data/processed/empirical/crypto_h2_exploratory_daily.csv"))
    output = repo / "data/processed/empirical/crypto_h2_nonoverlap_sensitivity.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run non-overlapping seven-day H2 return sensitivities")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()), indent=2))
