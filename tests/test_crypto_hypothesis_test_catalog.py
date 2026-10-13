import unittest

from src.pipeline.crypto_hypothesis_test_catalog import ACTIVE, build, render


class Tests(unittest.TestCase):
    def test_catalog_covers_scope_and_documents_matrix_roles(self):
        findings = {"active_hypotheses": ACTIVE, "findings": {
            "H1": {"transaction_count_coefficient": .1, "transaction_count_exact_p": .2},
            "H2": {"pooled_market_cap_interaction": .3, "pooled_market_cap_exact_p": .4}
        }}
        strict = {"results": [{"specification": "pooled_market_cap", "strict_coefficient": .2, "strict_p": .5}]}
        h3 = {"events_estimated": 2, "events_by_asset": {"crypto_arb": 1, "crypto_bnb": 1}, "mean_direction_adjusted_primary_car": -.1, "events_matching_predicted_sign": 1, "asset_sign_flip_p_two_sided": .5}
        h4 = {"consensus_assets_ready": 1, "case_studies_ready": 1, "pooled_estimation_ready": False}
        h8 = {"best_single_group_model": "bundle_x", "best_single_group_loo_rmse": 1.0, "raw_breadth_loo_rmse": 1.2}
        rows = build(findings, strict, h3, h4, h8)
        self.assertEqual([row["hypothesis"] for row in rows], ACTIVE)
        self.assertTrue(all(row["matrix_role"] and row["input_files"] and row["output_files"] for row in rows))
        self.assertIn("classification matrix", render(rows))

    def test_rejects_scope_drift(self):
        with self.assertRaises(ValueError):
            build({"active_hypotheses": ["H1"]}, {}, {}, {}, {})


if __name__ == "__main__":
    unittest.main()
