from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


GROUP_LABELS = {
    "monetary_store": "money or store-of-value use",
    "transaction_service_demand": "transaction and service demand",
    "security_commitment": "staked security commitment",
    "supply_absorption": "supply reduction or absorption",
    "financial_integration": "collateral and financial integration",
    "control_rights": "governance and control rights",
    "holder_capture": "direct holder or token capture",
    "subsidized_participation": "subsidized participation",
}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def active_groups(row: dict[str, str]) -> set[str]:
    return {key.removeprefix("bundle_") for key, value in row.items() if key.startswith("bundle_") and value == "1"}


def channels(groups: set[str]) -> list[str]:
    order = ["monetary_store", "transaction_service_demand", "security_commitment", "supply_absorption", "financial_integration", "holder_capture"]
    return [GROUP_LABELS[group] for group in order if group in groups]


def cautions(row: dict[str, str], groups: set[str]) -> list[str]:
    result: list[str] = []
    if "holder_capture" not in groups:
        result.append("No verified direct route from protocol value to the token or holder.")
    if "control_rights" in groups and "holder_capture" not in groups:
        result.append("Governance authority must not be described as holder value capture.")
    if "subsidized_participation" in groups:
        result.append("Some participation is subsidized; persistence without incentives requires separate testing.")
    if row["va_scarcity"] == "0":
        result.append("No verified hard cap or deterministic terminal supply bound.")
    if "security_commitment" in groups:
        result.append("Staking introduces lock-up, exit, validator, or protocol-risk considerations.")
    return result or ["No additional rule-based caution beyond the standard market, custody, liquidity, and regulatory review."]


def build(rows: list[dict[str, str]]) -> dict[str, Any]:
    if len(rows) != 23 or any(row.get("classification_status") != "complete_human_verified" for row in rows):
        raise ValueError("advisory profiles require the complete 23-asset verified matrix")
    group_map = {row["asset_id"]: active_groups(row) for row in rows}
    profiles=[]
    for row in rows:
        groups=group_map[row["asset_id"]]
        peers=[]
        for other in rows:
            if other["asset_id"] == row["asset_id"]: continue
            other_groups=group_map[other["asset_id"]]
            union=groups | other_groups
            similarity=len(groups & other_groups)/len(union) if union else 0
            peers.append((similarity, other["symbol"], sorted(groups & other_groups)))
        peers.sort(key=lambda item:(-item[0],item[1]))
        profiles.append({
            "asset_id": row["asset_id"], "symbol": row["symbol"], "architecture_context": row["architecture_context"],
            "economic_identity": [GROUP_LABELS[group] for group in GROUP_LABELS if group in groups],
            "potential_value_channels": channels(groups),
            "key_cautions": cautions(row,groups),
            "closest_economic_comparables": [{"symbol":symbol,"shared_functions":[GROUP_LABELS[g] for g in shared],"similarity":round(score,3)} for score,symbol,shared in peers[:3]],
            "advisory_action": "Compare the asset with its economic peers, verify that each mechanism is live on the decision date, and assess market, custody, liquidity, legal, and concentration risks separately.",
            "investment_score": None,
        })
    return {"status":"crypto_advisory_profiles_complete","assets":len(profiles),"purpose":"Economic due diligence and comparable selection; not investment recommendations or rankings.","profiles":profiles}


def render(result: dict[str, Any]) -> str:
    out=["# Cryptoasset advisory profiles", "", "These profiles translate the verified economic-function matrix into a practical advisory starting point. They do not assign investment scores, price targets, or recommendations.", ""]
    for p in result["profiles"]:
        out += [f"## {p['symbol']}", "", f"**Architecture context:** {p['architecture_context']}", "", f"**Economic identity:** {'; '.join(p['economic_identity']) or 'No active economic-function group.'}", "", f"**Potential value channels:** {'; '.join(p['potential_value_channels']) or 'No direct value channel verified under the current rules.'}", "", "**Key cautions:**"]
        out += [f"- {item}" for item in p["key_cautions"]]
        peers=", ".join(f"{peer['symbol']} ({', '.join(peer['shared_functions'])})" for peer in p["closest_economic_comparables"])
        out += ["", f"**Closest economic comparables:** {peers}", "", f"**Advisory action:** {p['advisory_action']}", ""]
    return "\n".join(out)


def run(repo: Path) -> dict[str, Any]:
    result=build(read_rows(repo/"data/processed/01_classification/crypto_verified_universe_profiles.csv"))
    out=repo/"data/processed/02_valuation/crypto_advisory_profiles.json"; out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    report=repo/"research/findings/crypto-advisory-profiles.md"; report.write_text(render(result),encoding="utf-8")
    return result


if __name__=="__main__":
    parser=argparse.ArgumentParser(description="Build plain-language advisory profiles from the verified function matrix")
    parser.add_argument("--repo",type=Path,default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()),indent=2))
