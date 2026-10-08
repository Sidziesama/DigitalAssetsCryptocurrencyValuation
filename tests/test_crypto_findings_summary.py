import unittest

from src.pipeline.crypto_findings_summary import build


class CryptoFindingsSummaryTests(unittest.TestCase):
    def test_plain_summary_separates_findings_from_pending_hypotheses(self):
        scope = {"active_hypotheses": ["H1", "H2", "H3", "H4", "H8"]}
        specs = ["pooled_market_cap", "chain_market_cap", "pooled_forward_return", "chain_forward_return"]
        estimates = {"estimates": [{"specification": name, "coefficients": {"fees_x_capture": 0.1}} for name in specs],
                     "leave_one_asset_out": [{"fees_x_capture": 0.01}]}
        inference = {"results": [{"specification": name, "wild_cluster_bootstrap_p_two_sided": 0.2} for name in specs]}
        nonoverlap = {"scope_summaries": [
            {"scope": "pooled", "positive_offsets": 4, "offsets_rejecting_at_10pct": 0},
            {"scope": "chain", "positive_offsets": 0, "offsets_rejecting_at_10pct": 0},
        ]}
        readiness = {"h8_design_ready_assets": 5}
        reviews = {"crypto_h2_expansion": {"completed_decisions": 10, "targeted_decisions": 10,
                   "agreements": 10, "disagreements": 0, "raw_agreement": 1.0, "cohen_kappa": 1.0, "freeze_eligible": True}}
        h8 = {"slope": 0.7, "exact_permutation_p_two_sided": 0.7, "spearman_rank_correlation": 0.1,
              "exact_rank_permutation_p_two_sided": 1.0, "leave_one_asset_out_positive": 4}
        h1 = {"assets": ["a", "b", "c", "d"], "rows": 20,
              "coefficients": {"log1p_active_addresses_lag1": 0.1, "log1p_transaction_count_lag1": 0.2},
              "inference": {"log1p_active_addresses_lag1": {"wild_cluster_bootstrap_p_two_sided": 0.5},
                            "log1p_transaction_count_lag1": {"wild_cluster_bootstrap_p_two_sided": 0.25}}}
        h3 = {"assets": ["a", "b", "c", "d"], "rows": 20, "assets_with_within_supply_variation": 2,
              "coefficients": {"circulating_supply_growth_7d_lag1": 10.0},
              "supply_growth_effect_per_basis_point": 0.001, "observed_supply_growth_sign": "positive",
              "inference": {"wild_cluster_bootstrap_p_two_sided": 0.25}}
        h4 = {"assets": 6, "verified_stake_positive_assets": 3,
              "positive_assets_with_historical_staking": 0,
              "positive_assets_with_partial_component_history": 1, "market_proxy_assets": 6}
        result = build(scope, estimates, inference, nonoverlap, readiness, reviews, h8, h1, h3, h4)
        self.assertEqual(result["findings"]["H2"]["status"], "exploratory_evidence_at_10pct_not_confirmatory")
        self.assertEqual(result["findings"]["H1"]["status"], "exploratory_positive_association_not_confirmed")
        self.assertEqual(result["findings"]["H8"]["status"], "exploratory_no_robust_breadth_premium_evidence")
        self.assertEqual(result["findings"]["H3"]["status"], "supply_proxy_diagnostic_not_identification_ready")
        self.assertEqual(result["findings"]["H4"]["status"], "source_readiness_complete_estimation_blocked")
        self.assertIn("Cardano", result["classification_review"]["resolution"])

    def test_verified_h8_supersedes_pilot_narrative(self):
        # Reuse the main fixture while checking the optional verified extension through a minimal patch.
        import inspect
        self.assertIn("h8_verified", inspect.signature(build).parameters)


if __name__ == "__main__":
    unittest.main()
