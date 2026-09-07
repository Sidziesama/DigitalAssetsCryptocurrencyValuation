import unittest

from src.pipeline.crypto_function_risk_exposure import (benjamini_hochberg, build, max_drawdown,
                                                        provisional_features, validate)

PREDICTORS = ["bundle_monetary_store", "bundle_control_rights", "raw_function_breadth"]


def spec(draws=200):
    return {"schema_version": 1, "document_version": "test", "status": "frozen_before_risk_estimation",
            "freeze_date": "2026-09-07", "experiment_id": "P1_H6", "panel": "p", "verified_profiles": "v",
            "provisional_design": "d", "bundle_map": "b",
            "window": {"start": "2024-01-01", "end": "2024-03-10", "expected_days": 70, "minimum_coverage_share": 0.9},
            "samples": [{"id": "verified_core", "source": "verified_profiles", "evidence_status": "evidence_verified",
                         "rule": "r", "inference": "exact_permutation"},
                        {"id": "provisional_universe", "source": "provisional_design",
                         "evidence_status": "provisional", "rule": "r", "inference": "monte_carlo_permutation"}],
            "outcomes": {"market_beta": "b", "realized_volatility_annualized": "v", "max_drawdown_log": "d"},
            "predictors": PREDICTORS, "control": "mean_log_dollar_volume",
            "model": "m", "inference": {"exact_permutation_assignments": 720, "monte_carlo_draws": draws,
                                        "random_seed": 1, "rule": "r", "multiple_testing": "bh"},
            "selection_rule": "s", "interpretation": "i", "prohibited": "p"}


def panel(days=70):
    from datetime import date, timedelta
    rows = []
    first = date(2024, 1, 1)
    volumes = [12.0, 10.5, 13.0, 11.0, 14.0, 10.0]
    for index, asset in enumerate(["a", "b", "c", "d", "e", "f"]):
        beta = 0.5 + 0.2 * index
        for day in range(days):
            market = 0.01 * ((day % 5) - 2)
            rows.append({"asset_id": asset, "date": (first + timedelta(days=day)).isoformat(),
                         "log_return": str(beta * market), "market_ew_log_return": str(market),
                         "log_dollar_volume": str(volumes[index])})
    return rows


def profiles():
    return [{"asset_id": asset, "classification_status": "complete_verified",
             "bundle_monetary_store": "1" if asset in ("a", "b", "c") else "0",
             "bundle_control_rights": "1", "raw_function_breadth": str(index + 1)}
            for index, asset in enumerate(["a", "b", "c", "d", "e", "f"])]


def design():
    return {"value_accrual_codes": ["VA_MONETARY", "VA_SCARCITY", "VA_GOV"],
            "assets": [{"asset_id": asset, "codes": [1 if index < 3 else 0, 0, 1]}
                       for index, asset in enumerate(["a", "b", "c", "d", "e", "f"])]}


def bundle_map():
    return {"bundles": {"monetary_store": ["VA_MONETARY", "VA_SCARCITY"], "control_rights": ["VA_GOV"]}}


class CryptoFunctionRiskExposureTests(unittest.TestCase):
    def test_recovers_planted_beta_ordering(self):
        assets, results, summary = build(spec(), panel(), profiles(), design(), bundle_map())
        self.assertEqual(len(assets), 12)
        core = {row["asset_id"]: row for row in assets if row["sample"] == "verified_core"}
        self.assertAlmostEqual(core["a"]["market_beta"], 0.5, places=6)
        self.assertAlmostEqual(core["f"]["market_beta"], 1.5, places=6)
        beta = [r for r in results if r["sample"] == "verified_core"
                and r["outcome"] == "market_beta" and r["predictor"] == "bundle_monetary_store"][0]
        self.assertLess(beta["coefficient"], 0)
        self.assertEqual(beta["permutation_assignments"], 720)
        self.assertEqual(len(summary["samples"]), 2)

    def test_constant_predictor_is_unestimable_not_dropped(self):
        _, results, summary = build(spec(), panel(), profiles(), design(), bundle_map())
        control = [r for r in results if r["sample"] == "verified_core" and r["predictor"] == "bundle_control_rights"]
        self.assertEqual(len(control), 3)
        self.assertTrue(all(row["estimable"] == 0 for row in control))
        self.assertIn("bundle_control_rights", summary["samples"][0]["unestimable_predictors"])

    def test_monte_carlo_uses_declared_draws(self):
        _, results, _ = build(spec(draws=150), panel(), profiles(), design(), bundle_map())
        row = [r for r in results if r["sample"] == "provisional_universe" and r["estimable"]][0]
        self.assertEqual(row["permutation_assignments"], 150)

    def test_provisional_features_map_codes_to_bundles(self):
        features = provisional_features(design(), bundle_map(), PREDICTORS)
        self.assertEqual(features["a"]["bundle_monetary_store"], 1.0)
        self.assertEqual(features["d"]["bundle_monetary_store"], 0.0)
        self.assertEqual(features["a"]["raw_function_breadth"], 2.0)

    def test_helpers(self):
        self.assertAlmostEqual(max_drawdown([0.2, -0.5, 0.1]), -0.5)
        self.assertEqual(benjamini_hochberg([0.01, 0.5]), [0.02, 0.5])

    def test_invalid_specification_is_rejected(self):
        bad = spec()
        bad["samples"][0]["inference"] = "bootstrap"
        with self.assertRaisesRegex(ValueError, "unsupported inference"):
            validate(bad)


if __name__ == "__main__":
    unittest.main()
