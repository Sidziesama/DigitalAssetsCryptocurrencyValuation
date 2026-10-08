import csv
import json
import unittest
from pathlib import Path

from src.pipeline.crypto_verified_universe import build, run

REPO = Path(__file__).resolve().parents[1]


class CryptoVerifiedUniverseTests(unittest.TestCase):
    def test_complete_active_universe_and_groups(self):
        summary = run(REPO)
        self.assertEqual(summary["assets"], 23)
        self.assertEqual(summary["classification_cells"], 230)
        self.assertEqual(summary["excluded_assets"], ["crypto_doge", "crypto_xmr"])
        self.assertEqual(set(summary["group_counts"]), {
            "monetary_store", "transaction_service_demand", "security_commitment",
            "supply_absorption", "financial_integration", "control_rights",
            "holder_capture", "subsidized_participation"})

    def test_unresolved_active_cell_is_rejected(self):
        load = lambda name: json.loads((REPO / "config" / name).read_text())
        with (REPO / "data/processed/01_classification/crypto_economic_design_targeted_review.csv").open(newline="") as handle:
            review = list(csv.DictReader(handle))
        next(row for row in review if row["asset_id"] == "crypto_btc")["decision_0_or_1"] = ""
        with self.assertRaisesRegex(ValueError, "unresolved"):
            build(load("assets.json"), load("research_scope.json"), load("crypto_economic_design.json"),
                  load("crypto_phase1_taxonomy.json"), review)


if __name__ == "__main__":
    unittest.main()
