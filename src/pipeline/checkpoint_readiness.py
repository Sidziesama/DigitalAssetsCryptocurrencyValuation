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
    h2_h8 = load_json(repo / "data/processed/evidence/crypto_h2_h8_pilot_readiness.json")
    h2_panel = load_json(repo / "data/processed/empirical/crypto_h2_exploratory_summary.json")
    h8_plan = load_json(repo / "data/processed/evidence/crypto_h8_evidence_plan_summary.json")
    fee_layer = load_json(repo / "data/processed/empirical/crypto_fee_fundamentals_summary.json")
    h2_diagnostics = load_json(repo / "data/processed/empirical/crypto_h2_estimator_diagnostics.json")
    h2_estimates = load_json(repo / "data/processed/empirical/crypto_h2_exploratory_estimates.json")
    blockers = load_json(repo / "data/processed/evidence/crypto_evidence_blockers_summary.json")

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
        "h2_pilot_design_ready": h2_h8["h2_design_ready_assets"] == evidence["assets"],
        "h8_five_asset_design_ready": h2_h8["h8_design_ready_assets"] == 5,
        "verified_negative_collateral_reconciles": all(
            row["asset_id"] in collateral["verified_below_threshold_assets"]
            for row in decisions
            if row["code"] == "VA_COLLATERAL" and row["status"] == "verified" and row["recommended_value"] == "0"
        ),
        "h2_candidate_panel_guarded": h2_panel["status"] == "candidate_h2_fee_panel_ready_preregistration_freeze_pending" and h2_panel["scope_design_predeclared"] is True and bool(h2_panel["primary_h2_blocker"]),
        "h2_estimator_diagnostics_pass": h2_diagnostics["status"] == "pass_with_small_sample_limits" and all(item["full_rank"] and item["balanced_panel"] for item in h2_diagnostics["diagnostics"]) and all(item["full_rank"] for item in h2_diagnostics["leave_one_asset_out"]),
        "h2_exploratory_estimates_guarded": h2_estimates["status"] == "exploratory_point_estimates_only" and all(item["standard_errors"] is None and item["p_values"] is None for item in h2_estimates["estimates"]),
        "bnb_blockers_documented": blockers["status"] == "documented_open_blockers" and blockers["open_blockers"] == 2 and blockers["assets_affected"] == ["crypto_bnb"],
        "h8_extension_plan_complete": h8_plan["status"] == "six_code_evidence_complete" and h8_plan["targeted_decisions"] == 36 and h8_plan["verified_decisions"] == 36 and h8_plan["pending_decisions"] == 0 and h8_plan["verified_mismatches"] == 0,
        "free_fee_layer_complete": fee_layer["complete_fee_assets"] == 6 and fee_layer["complete_revenue_assets"] == 6,
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
            "verified_below_collateral_threshold_assets": collateral["verified_below_threshold_assets"],
        },
        "stablecoin_evidence": {
            "temporally_eligible_assets": stablecoin["assets_with_post_score_outcomes"],
            "post_score_outcome_rows": stablecoin["post_score_outcome_rows"],
            "status": stablecoin["status"],
        },
        "model_readiness": {
            "h2": "guarded six-asset exploratory point estimates available without p-values; preregistration freeze required before confirmatory inference",
            "h8": "five-asset complete-case design ready; BNB withheld under documented monetary and collateral evidence blockers",
            "h5_h6": "temporal_overlap_ready_but_targeted_component_review_required_before_estimation",
        },
        "guardrails": [
            "Unknown or unsupported provider coverage remains null and is never encoded as zero.",
            "DeFiLlama supplied balances are a screen, not collateral-eligibility proof.",
            "Point-in-time design evidence cannot be backfilled into earlier outcome dates.",
            "This checkpoint validates methods and evidence provenance; it does not report hypothesis-test results.",
        ],
        "next_checkpoint": "Approve the documented BNB complete-case exclusion and freeze the H2/H8 pilot before adding confirmatory inference.",
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
