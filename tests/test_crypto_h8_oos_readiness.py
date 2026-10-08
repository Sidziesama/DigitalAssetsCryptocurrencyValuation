import unittest

from src.pipeline.crypto_h8_oos_readiness import build, validate


def specs():
    discovery = {"expected_assets": 23, "measurement_window": {"end": "2026-08-22"}}
    validation = {
        "status": "frozen_before_validation_outcomes",
        "document_version": "test",
        "expected_assets": 23,
        "validation_window": {"start": "2026-08-23", "end": "2027-08-22", "minimum_coverage_share": 0.8},
        "candidate_model": {"id": "bundle_financial_integration"},
        "benchmark_model": {"id": "raw_function_breadth"},
        "primary_metric": "leave_one_asset_out_root_mean_squared_prediction_error",
        "decision_rule": "fixed"
    }
    return validation, discovery


class Tests(unittest.TestCase):
    def test_validation_window_cannot_overlap_discovery(self):
        validation, discovery = specs()
        validation["validation_window"]["start"] = "2026-08-22"
        with self.assertRaises(ValueError):
            validate(validation, discovery)

    def test_candidate_group_cannot_be_reselected(self):
        validation, discovery = specs()
        validation["candidate_model"]["id"] = "bundle_holder_capture"
        with self.assertRaises(ValueError):
            validate(validation, discovery)

    def test_readiness_counts_only_fixed_window(self):
        validation, discovery = specs()
        observed = {"crypto_btc": {"2026-08-22", "2026-08-23", "2027-08-22"}}
        result = build(validation, discovery, observed)
        self.assertEqual(result["expected_calendar_days"], 365)
        self.assertEqual(result["minimum_days_per_asset"], 292)
        self.assertEqual(result["coverage"][0]["observed_days"], 2)
        self.assertEqual(result["status"], "waiting_for_fixed_validation_window")


if __name__ == "__main__":
    unittest.main()
