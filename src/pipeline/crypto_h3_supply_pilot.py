from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

from src.pipeline.crypto_h2_exploratory_estimates import estimate
from src.pipeline.crypto_h2_small_cluster_inference import wild_cluster_test


ASSETS = ("crypto_btc", "crypto_eth", "crypto_uni", "crypto_aave")
COLUMNS = ("circulating_supply_growth_7d_lag1", "log1p_active_addresses_lag1", "log1p_transaction_count_lag1")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build_panel(
    fundamentals: list[dict[str, str]], market: list[dict[str, str]]
) -> list[dict[str, Any]]:
    supply: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for row in fundamentals:
        if row.get("asset_id") not in ASSETS:
            continue
        try:
            value = float(row["current_supply"])
        except (KeyError, TypeError, ValueError):
            continue
        if value > 0:
            supply[row["asset_id"]].append((row["date"], value))

    growth = {}
    for asset_id, observations in supply.items():
        ordered = sorted(observations)
        for index in range(8, len(ordered)):
            date, lag1_supply = ordered[index - 1]
            _, lag8_supply = ordered[index - 8]
            target_date = ordered[index][0]
            growth[(asset_id, target_date)] = math.log(lag1_supply / lag8_supply)

    panel = []
    for row in market:
        key = (row.get("asset_id", ""), row.get("date", ""))
        if key not in growth:
            continue
        try:
            values = {
                "forward_log_return_7d": float(row["forward_log_return_7d"]),
                "log1p_active_addresses_lag1": float(row["log1p_active_addresses_lag1"]),
                "log1p_transaction_count_lag1": float(row["log1p_transaction_count_lag1"]),
            }
        except (KeyError, TypeError, ValueError):
            continue
        panel.append({
            "asset_id": key[0], "date": key[1],
            "circulating_supply_growth_7d_lag1": growth[key], **values,
        })
    return sorted(panel, key=lambda row: (row["date"], row["asset_id"]))


def build(rows: list[dict[str, Any]]) -> dict[str, Any]:
    assets = sorted({row["asset_id"] for row in rows})
    if assets != sorted(ASSETS):
        raise ValueError("H3 pilot requires the fixed four-asset Coin Metrics supply sample")
    primary = estimate("h3_supply_growth_forward_return", rows, "forward_log_return_7d", COLUMNS)
    inference = wild_cluster_test(
        rows, "forward_log_return_7d", COLUMNS, target="circulating_supply_growth_7d_lag1"
    )
    variation = []
    for asset_id in assets:
        values = [row["circulating_supply_growth_7d_lag1"] for row in rows if row["asset_id"] == asset_id]
        variation.append({
            "asset_id": asset_id, "observations": len(values),
            "minimum": min(values), "maximum": max(values),
            "nonzero_observations": sum(value != 0 for value in values),
            "unique_values": len(set(values)),
            "has_within_asset_variation": len(set(values)) > 1,
        })
    leave_one_out = []
    for asset_id in assets:
        result = estimate(
            f"h3_without_{asset_id}",
            [row for row in rows if row["asset_id"] != asset_id],
            "forward_log_return_7d", COLUMNS,
        )
        leave_one_out.append({
            "excluded_asset": asset_id,
            "supply_growth_coefficient": result["coefficients"]["circulating_supply_growth_7d_lag1"],
        })
    return {
        "status": "h3_supply_proxy_diagnostic_complete_not_identification_ready",
        "sample_rule": "Source-defined common Coin Metrics SplyCur coverage fixed to BTC, ETH, UNI, and AAVE.",
        "measure": "log change in reported circulating supply from t-8 through t-1",
        "outcome": "forward_log_return_7d from t through t+7",
        "rows": len(rows), "assets": assets,
        "dates": len({row["date"] for row in rows}),
        "coefficients": primary["coefficients"],
        "supply_growth_effect_per_basis_point": primary["coefficients"]["circulating_supply_growth_7d_lag1"] / 10000,
        "expected_h3_sign": "negative",
        "observed_supply_growth_sign": "positive" if primary["coefficients"]["circulating_supply_growth_7d_lag1"] > 0 else "negative",
        "within_r_squared": primary["within_r_squared"],
        "inference": inference,
        "variation_audit": variation,
        "assets_with_within_supply_variation": sum(row["has_within_asset_variation"] for row in variation),
        "leave_one_asset_out": leave_one_out,
        "guardrails": [
            "SplyCur is a reported circulating-supply measure; changes can reflect issuance, unlocks, burns, migrations, or provider methodology revisions.",
            "This pilot is not a clean scheduled-unlock event study and cannot identify which supply mechanism caused a change.",
            "The seven-day forward outcomes overlap, and four clusters provide only 16 exact sign assignments.",
            "Only BTC and ETH vary within the window; AAVE and UNI are flat under the provider measure, so the effective identifying support is two assets.",
            "Asset and date fixed effects plus lagged activity controls reduce confounding but do not establish causality.",
            "The source-defined four-asset sample cannot be expanded or selected based on coefficient results.",
        ],
    }


def run(repo: Path) -> dict[str, Any]:
    panel = build_panel(
        read_csv(repo / "data/processed/00_foundation/crypto_fundamentals_daily_coinmetrics.csv"),
        read_csv(repo / "data/processed/02_valuation/crypto_h2_exploratory_daily.csv"),
    )
    result = build(panel)
    output = repo / "data/processed/02_valuation/crypto_h3_supply_pilot.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    with (output.parent / "crypto_h3_supply_pilot.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(panel[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(panel)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Estimate the fixed four-asset exploratory H3 supply-growth pilot")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()), indent=2))
