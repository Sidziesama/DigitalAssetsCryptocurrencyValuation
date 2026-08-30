from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


EXPECTED = {
    ("crypto_bnb", "VA_MONETARY"): "pending_quantitative_behavior",
    ("crypto_bnb", "VA_COLLATERAL"): "pending_quantitative_threshold",
}


def build(config: dict[str, Any], decisions: list[dict[str, str]]) -> dict[str, Any]:
    blockers = config["blockers"]
    keys = [(row["asset_id"], row["code"]) for row in blockers]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate evidence blocker")
    if set(keys) != set(EXPECTED):
        raise ValueError("blocker manifest must contain exactly the two unresolved BNB decisions")
    unresolved = {
        (row["asset_id"], row["code"]): row["status"]
        for row in decisions
        if row["status"] != "verified"
    }
    if unresolved != EXPECTED:
        raise ValueError("blocker manifest no longer reconciles to unresolved evidence decisions")
    for row in blockers:
        key = (row["asset_id"], row["code"])
        if row["current_status"] != EXPECTED[key]:
            raise ValueError(f"stale blocker status for {key}")
        for field in ("required_evidence", "free_source_audit", "resolution_rule"):
            if not str(row.get(field, "")).strip():
                raise ValueError(f"missing {field} for {key}")
        if not row.get("acceptable_next_actions"):
            raise ValueError(f"missing acceptable next action for {key}")
    return {
        "status": "documented_open_blockers",
        "open_blockers": len(blockers),
        "assets_affected": sorted({row["asset_id"] for row in blockers}),
        "codes_affected": sorted({row["code"] for row in blockers}),
        "h8_policy": "retain null and estimate H8 on the five complete-case assets unless new evidence resolves BNB",
    }


def read_decisions(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def run(repo: Path) -> dict[str, Any]:
    config = json.loads((repo / "config/crypto_evidence_blockers.json").read_text(encoding="utf-8"))
    decisions = read_decisions(repo / "data/processed/evidence/crypto_design_evidence_tranche_1.csv")
    result = build(config, decisions)
    output = repo / "data/processed/evidence/crypto_evidence_blockers_summary.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit documented unresolved crypto evidence blockers")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()), indent=2))
