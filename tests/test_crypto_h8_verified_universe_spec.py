import json
import unittest
from pathlib import Path

from src.pipeline.crypto_economic_design import CODES

REPO = Path(__file__).resolve().parents[1]


class CryptoH8VerifiedUniverseSpecTests(unittest.TestCase):
    def setUp(self):
        self.spec = json.loads((REPO / "config/crypto_h8_verified_universe.json").read_text())

    def test_spec_is_frozen_before_estimation(self):
        self.assertEqual(self.spec["status"], "frozen_before_verified_universe_estimation")
        self.assertEqual(self.spec["hypothesis"], "H8")
        self.assertEqual(self.spec["expected_assets"], 23)
        self.assertEqual(self.spec["excluded_assets"], ["crypto_doge", "crypto_xmr"])

    def test_models_and_inference_are_fully_declared(self):
        self.assertEqual(len(self.spec["group_models"]), 8)
        self.assertEqual(len(self.spec["benchmark_models"]), 2)
        self.assertEqual(self.spec["inference"]["random_seed"], 20261008)
        self.assertEqual(self.spec["inference"]["multiple_testing"],
                         "benjamini_hochberg_false_discovery_rate_10_percent_across_eight_single_group_tests")
        self.assertTrue(self.spec["decision_rule"])
        self.assertGreaterEqual(len(self.spec["guardrails"]), 5)

    def test_group_partition_origin_is_the_ten_code_system(self):
        taxonomy = json.loads((REPO / "config/crypto_phase1_taxonomy.json").read_text())
        members = [code for group in taxonomy["bundles"].values() for code in group]
        self.assertEqual(set(members), set(CODES))
        self.assertEqual(len(members), len(CODES))


if __name__ == "__main__":
    unittest.main()
