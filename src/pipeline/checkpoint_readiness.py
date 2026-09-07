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
    small_cluster = load_json(repo / "data/processed/empirical/crypto_h2_small_cluster_inference.json")
    nonoverlap = load_json(repo / "data/processed/empirical/crypto_h2_nonoverlap_sensitivity.json")
    expansion = load_json(repo / "data/processed/evidence/crypto_h2_expansion_readiness.json")
    expansion_evidence = load_json(repo / "data/processed/evidence/crypto_h2_expansion_evidence_summary.json")
    reviews = load_json(repo / "data/processed/evidence/independent_review_summary.json")
    research_scope = load_json(repo / "data/processed/evidence/crypto_research_scope.json")
    h8_breadth = load_json(repo / "data/processed/empirical/crypto_h8_breadth_pilot.json")
    h8_extension = load_json(repo / "data/processed/empirical/crypto_h8_six_asset_extension.json")
    h1_activity = load_json(repo / "data/processed/empirical/crypto_h1_activity_pilot.json")
    h3_supply = load_json(repo / "data/processed/empirical/crypto_h3_supply_pilot.json")
    h4_readiness = load_json(repo / "data/processed/evidence/crypto_h4_source_readiness.json")
    h4_aave = load_json(repo / "data/processed/evidence/crypto_h4_aave_legacy_stake_summary.json")
    h4_bnb = load_json(repo / "data/processed/evidence/crypto_h4_bnb_stake_summary.json")
    h4_eth = load_json(repo / "data/processed/evidence/crypto_h4_eth_stake_summary.json")
    phase1_taxonomy = load_json(repo / "data/processed/evidence/crypto_phase1_taxonomy_summary.json")

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
        "mechanism_state_passes": mechanisms["status"] == "pass" and mechanisms["mismatches"] == 0 and mechanisms["resolved_asset_code_states"] == 22,
        "historical_collateral_state_available": collateral_state["assets"] >= 2,
        "h2_pilot_design_ready": h2_h8["h2_design_ready_assets"] == evidence["assets"],
        "h8_six_asset_design_ready": h2_h8["h8_design_ready_assets"] == 6,
        "verified_negative_collateral_reconciles": all(
            row["asset_id"] in collateral["verified_below_threshold_assets"]
            for row in decisions
            if row["code"] == "VA_COLLATERAL" and row["status"] == "verified" and row["recommended_value"] == "0"
        ),
        "h2_frozen_exploratory_panel_guarded": h2_panel["status"] == "frozen_exploratory_h2_fee_panel_ready" and h2_panel["preregistration_frozen"] is True and h2_panel["scope_design_predeclared"] is True and bool(h2_panel["primary_h2_blocker"]),
        "h2_extended_window_reconciles": h2_panel["market_assets"] == 11 and h2_panel["rows"] == 3971 and h2_panel["fee_level_eligible_rows"] == 3971 and h2_panel["fee_forward_return_eligible_rows"] == 3894 and fee_layer["start_date"] == "2025-08-25" and fee_layer["end_date"] == "2026-08-21",
        "h2_expansion_rule_passes": expansion["status"] == "expansion_ready" and expansion["candidates"] == 5 and expansion["selection_uses_model_outcomes"] is False,
        "h2_expansion_evidence_reconciles": expansion_evidence["status"] == "evidence_ready_review_complete" and expansion_evidence["targeted_decisions"] == 10 and expansion_evidence["event_matches"] == 10 and expansion_evidence["event_mismatches"] == 0 and expansion_evidence["independent_review_rows"] == 10 and expansion_evidence["independent_review_complete"] is True and expansion_evidence["preregistration_frozen"] is True,
        "active_crypto_scope_is_explicit": research_scope["status"] == "active_crypto_scope_valid" and research_scope["active_hypotheses"] == ["H1", "H2", "H3", "H4", "H8"] and research_scope["deferred_hypotheses"] == ["H5", "H6", "H7"] and research_scope["stablecoin_work_is_active_gate"] is False,
        "crypto_review_and_adjudication_complete": reviews["status"] == "active_crypto_review_complete" and reviews["crypto_h2_expansion"]["completed_decisions"] == 10 and reviews["crypto_h2_expansion"]["pending_decisions"] == 0 and reviews["crypto_h2_expansion"]["agreements"] == 10 and reviews["crypto_h2_expansion"]["disagreements"] == 0 and reviews["crypto_h2_expansion"]["freeze_eligible"] is True and reviews["stablecoin_h5_h6"]["active_gate"] is False,
        "h2_estimator_diagnostics_pass": h2_diagnostics["status"] == "pass_with_small_sample_limits" and all(item["full_rank"] and item["balanced_panel"] for item in h2_diagnostics["diagnostics"]) and all(item["full_rank"] for item in h2_diagnostics["leave_one_asset_out"]),
        "h2_exploratory_estimates_guarded": h2_estimates["status"] == "exploratory_point_estimates_only" and all(item["standard_errors"] is None and item["p_values"] is None for item in h2_estimates["estimates"]),
        "crypto_evidence_blockers_resolved": blockers["status"] == "evidence_complete_no_open_blockers" and blockers["open_blockers"] == 0,
        "h2_small_cluster_inference_guarded": small_cluster["status"] == "exploratory_small_cluster_inference_complete" and all(item["bootstrap_assignments"] == 2 ** item["clusters"] for item in small_cluster["results"]) and all(item["overlapping_outcome"] == (item["outcome"] == "forward_log_return_7d") for item in small_cluster["results"]),
        "h2_nonoverlap_sensitivity_complete": nonoverlap["status"] == "nonoverlapping_forward_return_sensitivity_complete" and len(nonoverlap["results"]) == 14 and all(item["offsets"] == 7 for item in nonoverlap["scope_summaries"]),
        "h8_extension_plan_complete": h8_plan["status"] == "six_code_evidence_complete" and h8_plan["targeted_decisions"] == 36 and h8_plan["verified_decisions"] == 36 and h8_plan["pending_decisions"] == 0 and h8_plan["verified_mismatches"] == 0,
        "h8_breadth_pilot_complete": h8_breadth["status"] == "exploratory_five_asset_h8_complete" and h8_breadth["assets"] == 5 and h8_breadth["permutations"] == 120 and len(h8_breadth["leave_one_asset_out"]) == 5,
        "h8_six_asset_extension_complete": h8_extension["status"] == "exploratory_six_asset_h8_extension_complete" and h8_extension["assets"] == 6 and h8_extension["permutations"] == 720 and len(h8_extension["leave_one_asset_out"]) == 6,
        "h1_activity_pilot_complete": h1_activity["status"] == "exploratory_four_asset_h1_complete" and h1_activity["rows"] == 352 and len(h1_activity["assets"]) == 4 and all(item["bootstrap_assignments"] == 16 for item in h1_activity["inference"].values()),
        "h3_supply_proxy_limit_documented": h3_supply["status"] == "h3_supply_proxy_diagnostic_complete_not_identification_ready" and h3_supply["rows"] == 296 and len(h3_supply["assets"]) == 4 and h3_supply["assets_with_within_supply_variation"] == 2 and h3_supply["inference"]["bootstrap_assignments"] == 16,
        "h4_source_blocker_documented": h4_readiness["status"] == "h4_source_readiness_complete_estimation_blocked" and h4_readiness["assets"] == 6 and h4_readiness["verified_stake_positive_assets"] == 3 and h4_readiness["positive_assets_with_historical_staking"] == 1 and h4_readiness["positive_assets_with_partial_component_history"] == 2 and h4_readiness["market_proxy_assets"] == 6 and h4_readiness["identification_ready"] is False,
        "h4_aave_component_complete_but_nonreleasing": h4_aave["status"] == "aave_legacy_stake_component_complete" and h4_aave["observed_days"] == 90 and h4_aave["unblocks_h4"] is False and h4_aave["measurement_role"] == "legacy_component_only",
        "h4_bnb_consensus_history_complete": h4_bnb["status"] == "bnb_consensus_stake_window_complete" and h4_bnb["observed_days"] == 90 and h4_bnb["unblocks_h4"] is True and not h4_bnb["failures"],
        "h4_eth_exact_collector_ready": h4_eth["status"] in {"eth_collector_ready_archive_endpoint_required", "eth_collector_ready_archive_endpoint_configured"} and h4_eth["measurement_role"] == "consensus_active_effective_balance" and h4_eth["unblocks_h4"] is False,
        "phase1_taxonomy_complete": phase1_taxonomy["status"] == "phase1_taxonomy_complete" and phase1_taxonomy["core_assets"] == 6 and phase1_taxonomy["complete_verified_assets"] == 6 and phase1_taxonomy["verified_decisions"] == 60 and phase1_taxonomy["consistency_cases_open"] == 0 and phase1_taxonomy["adjudicated_decisions"] == 1 and phase1_taxonomy["confirmatory_ready"] is False,
        "free_fee_layer_expansion_reconciles": fee_layer["assets"] == 11 and fee_layer["complete_fee_assets"] == 11 and fee_layer["complete_revenue_assets"] == 10 and fee_layer["complete_holders_revenue_assets"] == 9,
    }
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise ValueError(f"checkpoint readiness failed: {', '.join(failed)}")

    return {
        "as_of": "2026-08-31",
        "checkpoint": "frozen_exploratory_crypto_h2",
        "status": "commit_ready_frozen_exploratory_h2_checkpoint",
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
            "status": "preserved_deferred_not_an_active_gate",
        },
        "model_readiness": {
            "h2": "eleven-asset panel has exploratory 10%-level evidence of a positive valuation interaction after Cardano adjudication; post-pilot freeze and small-cluster limits prohibit confirmatory interpretation; no robust forward-return relationship",
            "h8": "the separately frozen six-asset extension remains positive in all leave-one-out samples, but exact permutation inference does not reject zero; breadth is more sign-stable but still not statistically established",
            "h1": "four-asset activity pilot has positive coefficients but exact inference does not reject zero; transaction association is leave-one-out sign-stable but not generalizable",
            "h3": "four-asset circulating-supply proxy diagnostic is complete, but only BTC and ETH vary; the positive, non-rejecting coefficient does not support H3 and is not identification-ready",
            "h4": "the six-asset universe is fixed; BNB history is complete, the exact ETH effective-balance collector is ready but needs an archival consensus endpoint, and legacy stkAAVE excludes Umbrella components, so estimation is blocked",
            "h5_h6_h7": "preserved for a deferred stablecoin phase and not an active gate",
        },
        "guardrails": [
            "Unknown or unsupported provider coverage remains null and is never encoded as zero.",
            "DeFiLlama supplied balances are a screen, not collateral-eligibility proof.",
            "Point-in-time design evidence cannot be backfilled into earlier outcome dates.",
            "This checkpoint validates methods and evidence provenance; it does not report hypothesis-test results.",
            "Cardano VA_PROTOCOL is adjudicated zero under the holder-directed mechanical-capture rule; the reviewed H2 specification is frozen post-pilot for reproducibility.",
        ],
        "next_checkpoint": "Phase 1 classification and the six-asset H8 extension are complete. Resume H4 by configuring an archival Ethereum consensus endpoint and completing Aave Umbrella coverage.",
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
