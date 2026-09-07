from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build(
    scope: dict[str, Any], estimates: dict[str, Any], inference: dict[str, Any],
    nonoverlap: dict[str, Any], readiness: dict[str, Any], reviews: dict[str, Any], h8: dict[str, Any],
    h1: dict[str, Any], h3: dict[str, Any], h4: dict[str, Any], h8_extension: dict[str, Any] | None = None
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
    return {
        "status": "crypto_findings_frozen_exploratory" if review_complete else "crypto_findings_current_adjudication_pending",
        "active_hypotheses": scope["active_hypotheses"],
        "headline": "Fee activity has a persistent positive association with valuation when active capture exists, but the evidence is exploratory and does not predict seven-day returns.",
        "findings": {
            "H1": {
                "status": "exploratory_positive_association_not_confirmed",
                "assets": len(h1["assets"]),
                "rows": h1["rows"],
                "active_addresses_coefficient": h1["coefficients"]["log1p_active_addresses_lag1"],
                "active_addresses_exact_p": h1["inference"]["log1p_active_addresses_lag1"]["wild_cluster_bootstrap_p_two_sided"],
                "transaction_count_coefficient": h1["coefficients"]["log1p_transaction_count_lag1"],
                "transaction_count_exact_p": h1["inference"]["log1p_transaction_count_lag1"]["wild_cluster_bootstrap_p_two_sided"],
                "plain_finding": "Active-address and transaction-count coefficients are positive in the four-asset panel, and transaction count remains positive in every leave-one-out sample. Exact four-cluster inference does not reject zero, so H1 remains suggestive and cannot be generalized beyond BTC, ETH, UNI, and AAVE.",
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
                "status": "supply_proxy_diagnostic_not_identification_ready",
                "assets": len(h3["assets"]), "rows": h3["rows"],
                "assets_with_within_supply_variation": h3["assets_with_within_supply_variation"],
                "supply_growth_coefficient": h3["coefficients"]["circulating_supply_growth_7d_lag1"],
                "effect_per_basis_point": h3["supply_growth_effect_per_basis_point"],
                "exact_p": h3["inference"]["wild_cluster_bootstrap_p_two_sided"],
                "observed_sign": h3["observed_supply_growth_sign"],
                "plain_finding": "The free circulating-supply diagnostic does not support H3: its coefficient is positive rather than the predicted negative and exact inference does not reject zero. More importantly, only BTC and ETH vary within the window, so a point-in-time unlock and issuance event panel is still required for an identification-ready test.",
            },
            "H4": {
                "status": "source_readiness_complete_estimation_blocked",
                "assets": h4["assets"],
                "verified_stake_positive_assets": h4["verified_stake_positive_assets"],
                "positive_assets_with_historical_staking": h4["positive_assets_with_historical_staking"],
                "positive_assets_with_partial_component_history": h4["positive_assets_with_partial_component_history"],
                "market_proxy_assets": h4["market_proxy_assets"],
                "plain_finding": "H4 is not yet estimable. A complete 90-day BNB consensus-staking series ranges from about 25.51m to 25.78m BNB. The exact ETH active-effective-balance collector is implemented but needs an archival consensus endpoint, while the legacy stkAAVE series excludes current Umbrella aToken/GHO stake. One complete positive-staking series remains insufficient to identify liquid-float effects.",
            },
            "H8": {
                "status": "exploratory_no_robust_breadth_premium_evidence",
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
                "plain_finding": "The frozen five-asset breadth result was positive but unstable. In the separately frozen six-asset extension, the slope remains positive and is positive in all six leave-one-out samples, but exact permutation inference does not reject zero. Breadth is more sign-stable after adding BNB, yet there is still no statistically robust valuation-premium evidence.",
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
        load("data/processed/evidence/crypto_research_scope.json"),
        load("data/processed/empirical/crypto_h2_exploratory_estimates.json"),
        load("data/processed/empirical/crypto_h2_small_cluster_inference.json"),
        load("data/processed/empirical/crypto_h2_nonoverlap_sensitivity.json"),
        load("data/processed/evidence/crypto_h2_h8_pilot_readiness.json"),
        load("data/processed/evidence/independent_review_summary.json"),
        load("data/processed/empirical/crypto_h8_breadth_pilot.json"),
        load("data/processed/empirical/crypto_h1_activity_pilot.json"),
        load("data/processed/empirical/crypto_h3_supply_pilot.json"),
        load("data/processed/evidence/crypto_h4_source_readiness.json"),
        load("data/processed/empirical/crypto_h8_six_asset_extension.json"),
    )
    output = repo / "data/processed/empirical/crypto_findings_summary.json"
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
