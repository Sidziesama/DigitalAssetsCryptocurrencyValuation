from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def evidence_values(*tranches: dict[str, Any]) -> dict[str, int]:
    values = {}
    for tranche in tranches:
        for row in tranche.get("decisions", []):
            if row.get("code") == "VA_STAKE" and row.get("status") == "verified":
                asset_id = row["asset_id"]
                if asset_id in values:
                    raise ValueError(f"duplicate VA_STAKE evidence for {asset_id}")
                values[asset_id] = int(row["recommended_value"])
    return values


def build(
    plan: dict[str, Any], verified: dict[str, int], market: list[dict[str, str]],
    components: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if plan.get("schema_version") != 1 or plan.get("hypothesis") != "H4":
        raise ValueError("unsupported H4 source plan")
    if plan.get("universe_policy") != "fixed_existing_six_assets_no_expansion":
        raise ValueError("H4 must retain the user-approved fixed six-asset universe")
    assets = plan.get("assets", [])
    ids = [row.get("asset_id") for row in assets]
    if len(ids) != 6 or len(ids) != len(set(ids)) or set(ids) != set(verified):
        raise ValueError("H4 plan must cover the exact six-asset verified VA_STAKE tranche")
    market_days = {}
    for row in market:
        if row.get("asset_id") in ids and row.get("volume_24h_usd") not in (None, "") and row.get("market_cap_usd") not in (None, ""):
            market_days[row["asset_id"]] = market_days.get(row["asset_id"], 0) + 1
    component_index = {row["asset_id"]: row for row in (components or [])}
    audit = []
    for row in assets:
        asset_id = row["asset_id"]
        if row.get("va_stake") not in (0, 1) or row["va_stake"] != verified[asset_id]:
            raise ValueError(f"H4 plan disagrees with verified VA_STAKE for {asset_id}")
        if not str(row.get("official_source_url", "")).startswith("https://"):
            raise ValueError(f"H4 plan lacks official HTTPS evidence for {asset_id}")
        status = row.get("historical_staked_supply_status")
        component = component_index.get(asset_id)
        minimum_days = int(plan.get("minimum_history_days", 365))
        positive_ready = row["va_stake"] == 1 and (
            status == "implemented" or bool(component and component.get("unblocks_h4") and component.get("observed_days", 0) >= minimum_days)
        )
        audit.append({**row, "market_proxy_days": market_days.get(asset_id, 0),
                      "partial_component_history": bool(component and component.get("observed_days", 0) > 0),
                      "staking_history_days": int(component.get("observed_days", 0)) if component else 0,
                      "minimum_history_days": minimum_days,
                      "positive_staking_history_ready": positive_ready})
    positives = [row for row in audit if row["va_stake"] == 1]
    ready_positives = sum(row["positive_staking_history_ready"] for row in positives)
    return {
        "status": "h4_source_readiness_complete_estimation_blocked",
        "assets": len(audit), "verified_stake_positive_assets": len(positives),
        "positive_assets_with_historical_staking": ready_positives,
        "positive_assets_with_partial_component_history": sum(row["va_stake"] == 1 and row["partial_component_history"] for row in audit),
        "market_proxy_assets": sum(row["market_proxy_days"] > 0 for row in audit),
        "identification_ready": ready_positives >= 3,
        "audit": audit,
        "blocker": f"Only {ready_positives} of {len(positives)} verified positive-staking assets has an implemented complete-window participation series; at least three are required by the readiness rule.",
        "required_next_data": [
            "effective-dated staked native units and total/circulating supply",
            "staking entry and exit timing or unbonding constraints",
            "same-date volume turnover plus spread/depth where freely reproducible",
            "separate consensus-stake and legacy AAVE-token risk-stake specifications",
        ],
        "guardrails": [
            "A verified VA_STAKE classification establishes mechanism presence, not the fraction staked.",
            "Reported 24-hour volume divided by market cap is a turnover proxy, not executable liquidity or liquid float.",
            "Consensus staking and legacy AAVE-token deficit-risk staking are not pooled without a predeclared comparability specification.",
            "Umbrella stakes aTokens and GHO rather than AAVE; its balances cannot fill a missing AAVE-denominated staking series.",
            "Structural zeros may be negative controls but cannot replace time variation among positive-staking assets.",
        ],
    }


def run(repo: Path) -> dict[str, Any]:
    load = lambda path: json.loads((repo / path).read_text(encoding="utf-8"))
    verified = evidence_values(load("config/crypto_h8_evidence_tranche_1.json"), load("config/crypto_h8_evidence_tranche_2.json"))
    result = build(load("config/crypto_h4_source_plan.json"), verified,
                   read_csv(repo / "data/processed/00_foundation/market_daily_coinpaprika.csv"),
                   [load("data/processed/01_classification/crypto_h4_aave_legacy_stake_summary.json"),
                    load("data/processed/01_classification/crypto_h4_bnb_stake_summary.json"),
                    load("data/processed/01_classification/crypto_h4_eth_stake_summary.json")])
    output = repo / "data/processed/01_classification/crypto_h4_source_readiness.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    with (output.parent / "crypto_h4_source_readiness.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(result["audit"][0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(result["audit"])
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit H4 historical staking and liquidity-source readiness")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()), indent=2))
