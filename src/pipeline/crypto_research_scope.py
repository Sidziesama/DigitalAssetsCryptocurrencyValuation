from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ACTIVE = ["H1", "H2", "H3", "H4", "H8"]
DEFERRED = ["H5", "H6", "H7"]


def validate(scope: dict[str, Any]) -> dict[str, Any]:
    if scope.get("schema_version") != 1:
        raise ValueError("unsupported research-scope schema")
    if scope.get("active_hypotheses") != ACTIVE:
        raise ValueError("active crypto hypotheses must remain H1, H2, H3, H4, and H8 in canonical order")
    deferred = scope.get("deferred_phase", {})
    if deferred.get("hypotheses") != DEFERRED or deferred.get("status") != "preserved_deferred_not_an_active_gate":
        raise ValueError("stablecoin H5-H7 must be preserved as a deferred non-gating phase")
    statuses = scope.get("hypothesis_status", {})
    if set(statuses) != set(ACTIVE) or any(not value for value in statuses.values()):
        raise ValueError("every active hypothesis requires an explicit readiness status")
    excluded = scope.get("excluded_assets", [])
    if not isinstance(excluded, list) or any(
        not isinstance(row, dict) or not row.get("asset_id") or not row.get("reason") or not row.get("effective_date")
        for row in excluded
    ):
        raise ValueError("every excluded asset requires an asset_id, reason, and effective_date")
    excluded_ids = [row["asset_id"] for row in excluded]
    if len(excluded_ids) != len(set(excluded_ids)):
        raise ValueError("excluded assets must be unique")
    return {
        "status": "active_crypto_scope_valid",
        "active_phase": scope["active_phase"],
        "active_hypotheses": ACTIVE,
        "deferred_hypotheses": DEFERRED,
        "stablecoin_work_preserved": True,
        "stablecoin_work_is_active_gate": False,
        "hypothesis_status": statuses,
        "communication_priority": scope["communication_priority"],
        "excluded_assets": excluded,
    }


def run(repo: Path) -> dict[str, Any]:
    scope = json.loads((repo / "config/research_scope.json").read_text(encoding="utf-8"))
    result = validate(scope)
    output = repo / "data/processed/01_classification/crypto_research_scope.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate the active crypto research phase and deferred stablecoin phase")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()), indent=2))
