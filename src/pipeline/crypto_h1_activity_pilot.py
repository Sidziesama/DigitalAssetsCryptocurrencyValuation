from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from src.pipeline.crypto_h2_exploratory_estimates import estimate
from src.pipeline.crypto_h2_small_cluster_inference import wild_cluster_test


COLUMNS = ("log1p_active_addresses_lag1", "log1p_transaction_count_lag1")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def eligible(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    selected = []
    for row in rows:
        try:
            values = {field: float(row[field]) for field in ("log_market_cap_usd", *COLUMNS)}
        except (KeyError, TypeError, ValueError):
            continue
        selected.append({**row, **values})
    return selected


def build(rows: list[dict[str, str]]) -> dict[str, Any]:
    sample = eligible(rows)
    assets = sorted({row["asset_id"] for row in sample})
    if len(assets) != 4:
        raise ValueError("H1 pilot requires the fixed four-asset common activity sample")
    primary = estimate("h1_common_activity_market_cap", sample, "log_market_cap_usd", COLUMNS)
    inference = {
        target: wild_cluster_test(sample, "log_market_cap_usd", COLUMNS, target=target)
        for target in COLUMNS
    }
    leave_one_out = []
    for asset_id in assets:
        subset = [row for row in sample if row["asset_id"] != asset_id]
        result = estimate(f"h1_without_{asset_id}", subset, "log_market_cap_usd", COLUMNS)
        leave_one_out.append({"excluded_asset": asset_id, **result["coefficients"]})
    return {
        "status": "exploratory_four_asset_h1_complete",
        "sample_rule": "Source-defined common Coin Metrics coverage fixed to BTC, ETH, UNI, and AAVE; it does not represent the broader crypto universe.",
        "rows": len(sample),
        "assets": assets,
        "dates": len({row["date"] for row in sample}),
        "outcome": "log_market_cap_usd",
        "coefficients": primary["coefficients"],
        "within_r_squared": primary["within_r_squared"],
        "inference": inference,
        "leave_one_asset_out": leave_one_out,
        "guardrails": [
            "Four clusters yield only 16 wild-cluster sign assignments and cannot support reliable generalization.",
            "Active addresses are ledger addresses, not unique users; transaction definitions remain provider-specific.",
            "Usage and valuation are jointly determined, so coefficients are associations rather than causal network effects.",
            "The four-asset source-defined sample cannot be selected or expanded based on coefficient results.",
        ],
    }


def run(repo: Path) -> dict[str, Any]:
    result = build(read_csv(repo / "data/processed/02_valuation/crypto_h2_exploratory_daily.csv"))
    output = repo / "data/processed/02_valuation/crypto_h1_activity_pilot.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    coefficient_rows = [
        {"variable": variable, "coefficient": coefficient,
         "wild_cluster_p_two_sided": result["inference"][variable]["wild_cluster_bootstrap_p_two_sided"]}
        for variable, coefficient in result["coefficients"].items()
    ]
    with (output.parent / "crypto_h1_activity_pilot.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(coefficient_rows[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(coefficient_rows)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Estimate the fixed four-asset exploratory H1 activity pilot")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()), indent=2))
