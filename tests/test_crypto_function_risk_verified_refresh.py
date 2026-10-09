import unittest

from src.pipeline.crypto_function_risk_verified_refresh import merged_spec, validate_profiles


def parent():
    return {
        "window": {"start": "a"}, "outcomes": {"risk": "x"}, "predictors": ["p"],
        "control": "size", "model": "ols", "inference": {"random_seed": 1},
        "provisional_design": "d", "bundle_map": "b", "status": "frozen_before_risk_estimation"
    }


def refresh():
    return {
        "status": "frozen_before_verified_input_refresh", "document_version": "v", "freeze_date": "2026-10-09",
        "experiment_id": "refresh", "verified_profiles": "profiles", "expected_classification_assets": 2,
        "expected_classification_status": "complete_human_verified",
        "sample": {"id": "verified_universe", "source": "verified_profiles", "evidence_status": "complete",
                   "inference": "monte_carlo_permutation"},
        "locked_from_parent": ["window", "outcomes", "predictors", "control", "model", "inference"],
        "interpretation": "not confirmatory"
    }


class Tests(unittest.TestCase):
    def test_only_input_and_sample_are_refreshed(self):
        result = merged_spec(refresh(), parent())
        self.assertEqual(result["window"], {"start": "a"})
        self.assertEqual(result["predictors"], ["p"])
        self.assertEqual(result["verified_profiles"], "profiles")
        self.assertEqual(len(result["samples"]), 1)

    def test_locked_fields_cannot_change(self):
        value = refresh()
        value["locked_from_parent"].remove("window")
        with self.assertRaises(ValueError):
            merged_spec(value, parent())

    def test_all_profiles_must_be_complete(self):
        rows = [{"asset_id": "a", "classification_status": "complete_human_verified"},
                {"asset_id": "b", "classification_status": "pending"}]
        with self.assertRaises(ValueError):
            validate_profiles(refresh(), rows)


if __name__ == "__main__":
    unittest.main()
