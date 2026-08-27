from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_readiness(repo: Path) -> dict[str, Any]:
    evidence = load_json(repo / "data/processed/evidence/crypto_design_evidence_tranche_1_summary.json")
    decisions_path = repo / "data/processed/evidence/crypto_design_evidence_tranche_1.csv"
    monetary = load_json(repo / "data/processed/evidence/crypto_monetary_assessment.json")
    collateral = load_json(repo / "data/processed/evidence/crypto_collateral_screen_summary.json")
    collateral_state = load_json(repo / "data/processed/evidence/aave_collateral_state_summary.json")
    mechanisms = load_json(repo / "data/processed/evidence/crypto_mechanism_state_summary.json")
    fundamentals = load_json(repo / "data/processed/empirical/crypto_fundamentals_summary.json")
    stablecoin = load_json(repo / "data/processed/evidence/stablecoin_h5_h6_temporal_readiness.json")

    with decisions_path.open(newline="", encoding="utf-8") as handle:
        decisions = list(csv.DictReader(handle))
    unresolved = [
        {"asset_id": row["asset_id"], "code": row["code"], "status": row["status"]}
        for row in decisions if row["status"] != "verified"
    ]

    checks = {
        "crypto_grid_complete": evidence["targeted_decisions"] == 24,
        "crypto_verified_counts_reconcile": evidence["verified_decisions"] + evidence["pending_decisions"] == evidence["targeted_decisions"],
        "crypto_no_verified_mismatches": evidence["verified_mismatches"] == 0,
        "unresolved_count_reconciles": len(unresolved) == evidence["pending_decisions"],
        "missing_activity_not_classified_negative": not (
            set(monetary["unresolved_assets"]) & set(monetary["verified_negative_assets"])
        ),
        "mechanism_state_passes": mechanisms["status"] == "pass" and mechanisms["mismatches"] == 0,
        "historical_collateral_state_available": collateral_state["assets"] >= 2,
        "stablecoin_temporal_overlap_ready": stablecoin["status"] == "temporal_overlap_ready",
    }
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise ValueError(f"checkpoint readiness failed: {', '.join(failed)}")

    return {
        "as_of": "2026-08-22",
        "checkpoint": "point_in_time_design_evidence_pilot",
        "status": "commit_ready_methodology_checkpoint_not_model_ready",
        "checks": checks,
        "crypto_evidence": {
            "assets": evidence["assets"],
            "targeted_decisions": evidence["targeted_decisions"],
            "verified_decisions": evidence["verified_decisions"],
            "pending_decisions": evidence["pending_decisions"],
            "coverage_ratio": evidence["coverage_ratio"],
            "unresolved": unresolved,
        },
        "source_coverage": {
            "free_fundamentals_assets_with_behavioral_coverage": fundamentals["monetary_behavior_coverage_pass"],
            "monetary_unresolved_assets": monetary["unresolved_assets"],
            "collateral_proxy_pass_assets": collateral["proxy_pass_assets"],
            "historical_collateral_state_assets": collateral_state["assets"],
            "effective_dated_mechanism_states": mechanisms["resolved_asset_code_states"],
        },
        "stablecoin_evidence": {
            "temporally_eligible_assets": stablecoin["assets_with_post_score_outcomes"],
            "post_score_outcome_rows": stablecoin["post_score_outcome_rows"],
            "status": stablecoin["status"],
        },
        "model_readiness": {
            "h2_h8": "not_ready_until_remaining_pilot_decisions_are_resolved_and_evidence_is_extended",
            "h5_h6": "temporal_overlap_ready_but_targeted_component_review_required_before_estimation",
        },
        "guardrails": [
            "Unknown or unsupported provider coverage remains null and is never encoded as zero.",
            "DeFiLlama supplied balances are a screen, not collateral-eligibility proof.",
            "Point-in-time design evidence cannot be backfilled into earlier outcome dates.",
            "This checkpoint validates methods and evidence provenance; it does not report hypothesis-test results.",
        ],
        "next_checkpoint": "Resolve the six remaining pilot decisions, freeze the focused review, and build the first estimation-ready H2/H8 panel.",
    }


def run(repo: Path) -> dict[str, Any]:
    result = build_readiness(repo)
    output = repo / "data/processed/evidence/point_in_time_design_checkpoint.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the consolidated point-in-time evidence checkpoint")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()), indent=2))
