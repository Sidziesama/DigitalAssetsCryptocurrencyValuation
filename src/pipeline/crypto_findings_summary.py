from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build(
    scope: dict[str, Any], estimates: dict[str, Any], inference: dict[str, Any],
    nonoverlap: dict[str, Any], readiness: dict[str, Any], reviews: dict[str, Any], h8: dict[str, Any],
    h1: dict[str, Any], h3: dict[str, Any], h4: dict[str, Any], h8_extension: dict[str, Any] | None = None,
    h8_verified: dict[str, Any] | None = None, h3_events: dict[str, Any] | None = None,
    h1_expansion: dict[str, Any] | None = None, h1_history: dict[str, Any] | None = None
) -> dict[str, Any]:
    if scope["active_hypotheses"] != ["H1", "H2", "H3", "H4", "H8"]:
        raise ValueError("findings summary requires the active crypto-only scope")
    estimate_index = {row["specification"]: row for row in estimates["estimates"]}
    inference_index = {row["specification"]: row for row in inference["results"]}
    pooled = estimate_index["pooled_market_cap"]
    chain = estimate_index["chain_market_cap"]
    pooled_return = estimate_index["pooled_forward_return"]
    chain_return = estimate_index["chain_forward_return"]
    pooled_inf = inference_index["pooled_market_cap"]
    chain_inf = inference_index["chain_market_cap"]
    pooled_return_inf = inference_index["pooled_forward_return"]
    chain_return_inf = inference_index["chain_forward_return"]
    scopes = {row["scope"]: row for row in nonoverlap["scope_summaries"]}
    review = reviews["crypto_h2_expansion"]
    if review["completed_decisions"] != 10:
        raise ValueError("crypto findings require the complete focused review")
    review_complete = review["freeze_eligible"] and review["disagreements"] == 0
    h1_main = h1_expansion["primary"] if h1_expansion else h1
    h1_assets = len(h1_main["assets"])
    h1_address = h1_main["coefficients"]["log1p_active_addresses_lag1"]
    h1_transactions = h1_main["coefficients"]["log1p_transaction_count_lag1"]
    h1_address_p = h1_main["inference"]["log1p_active_addresses_lag1"]["wild_cluster_bootstrap_p_two_sided"]
    h1_transactions_p = h1_main["inference"]["log1p_transaction_count_lag1"]["wild_cluster_bootstrap_p_two_sided"]
    return {
        "status": "crypto_findings_frozen_exploratory" if review_complete else "crypto_findings_current_adjudication_pending",
        "active_hypotheses": scope["active_hypotheses"],
        "headline": ("In the verified 23-asset classification universe, financial integration is the strongest single valuation indicator and modestly outpredicts raw function breadth; H2 fee-and-capture evidence remains definition-sensitive."
                     if h8_verified else "Fee activity has a persistent positive association with valuation when active capture exists, but the evidence is exploratory and does not predict seven-day returns."),
        "findings": {
            "H1": {
                "status": "one_year_retrospective_positive_suggestive_not_confirmed" if h1_history else "expanded_native_network_associations_mixed_not_confirmed" if h1_expansion else "exploratory_positive_association_not_confirmed",
                "assets": h1_assets,
                "rows": h1_main["rows"],
                "dates": h1_main.get("dates"),
                "active_addresses_coefficient": h1_address,
                "active_addresses_exact_p": h1_address_p,
                "transaction_count_coefficient": h1_transactions,
                "transaction_count_exact_p": h1_transactions_p,
                "pilot_transaction_count_coefficient": h1["coefficients"]["log1p_transaction_count_lag1"],
                "pilot_transaction_count_exact_p": h1["inference"]["log1p_transaction_count_lag1"]["wild_cluster_bootstrap_p_two_sided"],
                "one_year_active_addresses_coefficient": h1_history["primary"]["coefficients"]["log1p_active_addresses_lag1"] if h1_history else None,
                "one_year_active_addresses_exact_p": h1_history["primary"]["inference"]["log1p_active_addresses_lag1"]["wild_cluster_bootstrap_p_two_sided"] if h1_history else None,
                "one_year_transaction_count_coefficient": h1_history["primary"]["coefficients"]["log1p_transaction_count_lag1"] if h1_history else None,
                "one_year_transaction_count_exact_p": h1_history["primary"]["inference"]["log1p_transaction_count_lag1"]["wild_cluster_bootstrap_p_two_sided"] if h1_history else None,
                "plain_finding": (f"The frozen nine-native-network 90-day expansion gives a positive active-address coefficient ({h1_address:.4f}, exact p={h1_address_p:.3f}) and a negative transaction-count coefficient ({h1_transactions:.4f}, exact p={h1_transactions_p:.3f}). A retrospective one-year robustness extension makes both positive: active addresses {h1_history['primary']['coefficients']['log1p_active_addresses_lag1']:.4f} (p={h1_history['primary']['inference']['log1p_active_addresses_lag1']['wild_cluster_bootstrap_p_two_sided']:.3f}) and transactions {h1_history['primary']['coefficients']['log1p_transaction_count_lag1']:.4f} (p={h1_history['primary']['inference']['log1p_transaction_count_lag1']['wild_cluster_bootstrap_p_two_sided']:.3f}). The transaction sign turns negative without XLM, and the extension was specified after the short-window result, so H1 remains suggestive rather than confirmed."
                                  if h1_history else f"The frozen nine-native-network expansion gives a positive active-address coefficient ({h1_address:.4f}, exact p={h1_address_p:.3f}) and a negative transaction-count coefficient ({h1_transactions:.4f}, exact p={h1_transactions_p:.3f}). Neither is confirmed, and the active-address sign reverses when XLM is omitted. A twelve-asset sensitivity that mixes native-network and token-contract activity makes both coefficients positive, demonstrating measurement-scope sensitivity rather than stronger evidence for H1."
                                  if h1_expansion else "Active-address and transaction-count coefficients are positive in the four-asset panel, and transaction count remains positive in every leave-one-out sample. Exact four-cluster inference does not reject zero, so H1 remains suggestive and cannot be generalized beyond BTC, ETH, UNI, and AAVE."),
            },
            "H2": {
                "status": "exploratory_evidence_at_10pct_not_confirmatory",
                "pooled_market_cap_interaction": pooled["coefficients"]["fees_x_capture"],
                "pooled_market_cap_exact_p": pooled_inf["wild_cluster_bootstrap_p_two_sided"],
                "chain_market_cap_interaction": chain["coefficients"]["fees_x_capture"],
                "chain_market_cap_exact_p": chain_inf["wild_cluster_bootstrap_p_two_sided"],
                "pooled_forward_return_interaction": pooled_return["coefficients"]["fees_x_capture"],
                "pooled_forward_return_exact_p": pooled_return_inf["wild_cluster_bootstrap_p_two_sided"],
                "chain_forward_return_interaction": chain_return["coefficients"]["fees_x_capture"],
                "chain_forward_return_exact_p": chain_return_inf["wild_cluster_bootstrap_p_two_sided"],
                "leave_one_asset_out_positive": all(row["fees_x_capture"] > 0 for row in estimates["leave_one_asset_out"]),
                "nonoverlap_pooled_positive_offsets": scopes["pooled"]["positive_offsets"],
                "nonoverlap_chain_positive_offsets": scopes["chain"]["positive_offsets"],
                "nonoverlap_offsets_rejecting_10pct": scopes["pooled"]["offsets_rejecting_at_10pct"] + scopes["chain"]["offsets_rejecting_at_10pct"],
                "plain_finding": "Higher fees are more strongly associated with market value when active capture exists. The result is persistent across asset exclusions and crosses the 10% exploratory reference threshold, but the post-pilot freeze and small sample prevent confirmatory interpretation; there is no robust short-horizon return signal.",
            },
            "H3": {
                "status": "multiasset_supply_event_result_not_supported_low_power" if h3_events and len(h3_events.get("assets", [])) >= 2 else "supply_proxy_diagnostic_not_identification_ready",
                "assets": len(h3["assets"]), "rows": h3["rows"],
                "assets_with_within_supply_variation": h3["assets_with_within_supply_variation"],
                "supply_growth_coefficient": h3["coefficients"]["circulating_supply_growth_7d_lag1"],
                "effect_per_basis_point": h3["supply_growth_effect_per_basis_point"],
                "exact_p": h3["inference"]["wild_cluster_bootstrap_p_two_sided"],
                "observed_sign": h3["observed_supply_growth_sign"],
                "supply_events_estimated": h3_events["events_estimated"] if h3_events else 0,
                "supply_event_assets": h3_events["assets"] if h3_events else [],
                "supply_event_mean_primary_car": h3_events["mean_primary_car"] if h3_events else None,
                "supply_events_matching_negative_sign": h3_events["events_matching_negative_h3_sign"] if h3_events else None,
                "supply_event_mean_direction_adjusted_car": h3_events.get("mean_direction_adjusted_primary_car") if h3_events else None,
                "supply_events_matching_predicted_sign": h3_events.get("events_matching_predicted_sign") if h3_events else None,
                "supply_event_asset_sign_flip_p": h3_events.get("asset_sign_flip_p_two_sided") if h3_events else None,
                "plain_finding": (f"The multiasset supply-event study does not support H3. It estimates {h3_events['events_estimated']} material events across {len(h3_events['assets'])} assets. {'All asset-level average direction-adjusted returns oppose the hypothesis' if all(value <= 0 for value in h3_events['asset_mean_direction_adjusted_primary_car'].values()) else 'Asset-level average direction-adjusted returns are mixed'}; {h3_events['events_matching_predicted_sign']} of {h3_events['events_estimated']} events match the predicted sign, and the exact asset-level sign-flip p-value is {h3_events['asset_sign_flip_p_two_sided']:.3f}. With only {len(h3_events['assets'])} independent asset units, inference remains low-powered."
                                  if h3_events else "The free circulating-supply diagnostic does not support H3: its coefficient is positive rather than the predicted negative and exact inference does not reject zero. More importantly, only BTC and ETH vary within the window, so a point-in-time unlock and issuance event panel is still required for an identification-ready test."),
            },
            "H4": {
                "status": "source_readiness_complete_estimation_blocked",
                "assets": h4["assets"],
                "verified_stake_positive_assets": h4["verified_stake_positive_assets"],
                "positive_assets_with_historical_staking": h4["positive_assets_with_historical_staking"],
                "positive_assets_with_partial_component_history": h4["positive_assets_with_partial_component_history"],
                "market_proxy_assets": h4["market_proxy_assets"],
                "plain_finding": "H4 is not yet estimable as a comparative consensus-staking test. BNB now has 365 complete days and legacy stkAAVE has 365 days as a separate protocol-risk-stake case study. ETH has no historical observations because an archival consensus endpoint is still required. Umbrella balances are correctly excluded from the AAVE-token series because Umbrella stakes aTokens and GHO, not AAVE.",
            },
            "H8": {
                "status": "verified_universe_theory_groups_favored_exploratory" if h8_verified else "exploratory_no_robust_breadth_premium_evidence",
                "design_ready_assets": readiness["h8_design_ready_assets"],
                "raw_breadth_slope": h8["slope"],
                "exact_permutation_p_two_sided": h8["exact_permutation_p_two_sided"],
                "spearman_rank_correlation": h8["spearman_rank_correlation"],
                "exact_rank_permutation_p_two_sided": h8["exact_rank_permutation_p_two_sided"],
                "leave_one_asset_out_positive": h8["leave_one_asset_out_positive"],
                "six_asset_extension_slope": h8_extension["slope"] if h8_extension else None,
                "six_asset_extension_exact_p": h8_extension["exact_permutation_p_two_sided"] if h8_extension else None,
                "six_asset_extension_rank_correlation": h8_extension["spearman_rank_correlation"] if h8_extension else None,
                "six_asset_extension_rank_exact_p": h8_extension["exact_rank_permutation_p_two_sided"] if h8_extension else None,
                "six_asset_extension_leave_one_out_positive": h8_extension["leave_one_asset_out_positive"] if h8_extension else None,
                "verified_universe_assets": h8_verified["assets_in_classification_universe"] if h8_verified else None,
                "verified_universe_best_group": h8_verified["best_single_group_model"] if h8_verified else None,
                "verified_universe_best_group_loo_rmse": h8_verified["best_single_group_loo_rmse"] if h8_verified else None,
                "verified_universe_raw_breadth_loo_rmse": h8_verified["raw_breadth_loo_rmse"] if h8_verified else None,
                "verified_universe_fdr_rejections": h8_verified["fdr_10pct_rejections"] if h8_verified else [],
                "verified_universe_decision": h8_verified["decision_rule_result"] if h8_verified else None,
                "plain_finding": ("The 23-asset verified-universe extension favors theory-defined groups over raw function breadth. Financial integration is the best single predictor and modestly lowers leave-one-asset-out error; financial integration, monetary/store use, and supply absorption survive 10% false-discovery control. The result is exploratory, cross-sectional, and non-causal."
                                  if h8_verified else "The frozen five-asset breadth result was positive but unstable. In the separately frozen six-asset extension, the slope remains positive and is positive in all six leave-one-out samples, but exact permutation inference does not reject zero. Breadth is more sign-stable after adding BNB, yet there is still no statistically robust valuation-premium evidence."),
            },
        },
        "classification_review": {
            "decisions": review["targeted_decisions"],
            "agreements": review["agreements"],
            "disagreements": review["disagreements"],
            "raw_agreement": review["raw_agreement"],
            "cohen_kappa": review["cohen_kappa"],
            "resolution": "Cardano VA_PROTOCOL = 0. Ordinary staking rewards are service compensation, and governance treasury spending on ecosystem projects is VA_GOV rather than holder-directed protocol capture.",
        },
        "deferred": "Stablecoin H5, H6, and H7 are preserved for a separate later phase and do not gate these findings.",
        "interpretation_guardrail": "These are research findings about associations and evidence readiness, not causal claims, price targets, or investment recommendations.",
    }


def run(repo: Path) -> dict[str, Any]:
    def load(relative: str) -> dict[str, Any]:
        return json.loads((repo / relative).read_text(encoding="utf-8"))
    result = build(
        load("data/processed/01_classification/crypto_research_scope.json"),
        load("data/processed/02_valuation/crypto_h2_exploratory_estimates.json"),
        load("data/processed/02_valuation/crypto_h2_small_cluster_inference.json"),
        load("data/processed/02_valuation/crypto_h2_nonoverlap_sensitivity.json"),
        load("data/processed/01_classification/crypto_h2_h8_pilot_readiness.json"),
        load("data/processed/01_classification/independent_review_summary.json"),
        load("data/processed/02_valuation/crypto_h8_breadth_pilot.json"),
        load("data/processed/02_valuation/crypto_h1_activity_pilot.json"),
        load("data/processed/02_valuation/crypto_h3_supply_pilot.json"),
        load("data/processed/01_classification/crypto_h4_source_readiness.json"),
        load("data/processed/02_valuation/crypto_h8_six_asset_extension.json"),
        load("data/processed/02_valuation/crypto_h8_verified_universe_summary.json"),
        load("data/processed/02_valuation/crypto_h3_supply_event_analysis.json"),
        load("data/processed/02_valuation/crypto_h1_activity_expansion.json"),
        load("data/processed/02_valuation/crypto_h1_activity_history_analysis.json"),
    )
    output = repo / "data/processed/02_valuation/crypto_findings_summary.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    findings = repo / "research/findings/crypto-current-findings.md"
    findings.parent.mkdir(parents=True, exist_ok=True)
    h2 = result["findings"]["H2"]
    findings.write_text(
        "# Current Crypto Findings\n\n"
        f"**Headline:** {result['headline']}\n\n"
        f"- H2 pooled valuation interaction: {h2['pooled_market_cap_interaction']:.3f}; exact p-value: {h2['pooled_market_cap_exact_p']:.3f}.\n"
        f"- H2 chain valuation interaction: {h2['chain_market_cap_interaction']:.3f}; exact p-value: {h2['chain_market_cap_exact_p']:.3f}.\n"
        f"- All leave-one-asset-out valuation interactions positive: {h2['leave_one_asset_out_positive']}.\n"
        f"- Non-overlapping return offsets rejecting zero at 10%: {h2['nonoverlap_offsets_rejecting_10pct']}.\n\n"
        f"{h2['plain_finding']}\n\n"
        f"{result['findings']['H1']['plain_finding']} {result['findings']['H3']['plain_finding']} {result['findings']['H4']['plain_finding']} {result['findings']['H8']['plain_finding']} "
        "Stablecoin H5-H7 are deferred to a later phase.\n",
        encoding="utf-8",
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the plain-language current crypto findings summary")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()), indent=2))
