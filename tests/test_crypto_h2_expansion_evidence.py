import copy
import csv
import tempfile
import unittest
from pathlib import Path

from src.pipeline.crypto_h2_expansion_evidence import REVIEW_FIELDS, audit


class CryptoH2ExpansionEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.assets = [f"asset_{index}" for index in range(5)]
        self.codes = ["VA_BURN", "VA_PROTOCOL"]
        self.expansion = {
            "analysis_window": {"start": "2025-08-26"},
            "expansion_assets": self.assets,
            "requirements": {"required_mechanism_codes": self.codes},
        }
        self.decisions = [
            {"asset_id": asset, "code": code, "recommended_value": 1,
             "effective_from": "2025-01-01", "source_url": f"https://example.org/{asset}/{code}",
             "rationale": "Primary-source mechanism evidence."}
            for asset in self.assets for code in self.codes
        ]
        self.evidence = {"schema_version": 1, "assets": self.assets, "codes": self.codes,
                         "decisions": self.decisions}
        self.events = [
            {"asset_id": row["asset_id"], "code": row["code"], "value": row["recommended_value"],
             "effective_from": row["effective_from"], "source_url": row["source_url"],
             "rationale": row["rationale"]}
            for row in self.decisions
        ]

    def test_complete_grid_matches_ledger_and_blind_sheet_leaks_no_values(self):
        rows, review, summary = audit(self.evidence, self.expansion, self.events)
        self.assertEqual(summary["status"], "evidence_ready_independent_review_pending")
        self.assertEqual(summary["event_matches"], 10)
        self.assertTrue(all(row["event_match"] for row in rows))
        self.assertEqual(list(review[0]), REVIEW_FIELDS)
        self.assertTrue(all(row["reviewer_value"] == "" for row in review))
        self.assertFalse(any("recommended_value" in row for row in review))

    def test_missing_or_duplicate_decision_is_rejected(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["decisions"][-1] = copy.deepcopy(evidence["decisions"][0])
        with self.assertRaisesRegex(ValueError, "exactly one decision"):
            audit(evidence, self.expansion, self.events)

    def test_ledger_mismatch_blocks_evidence_status(self):
        events = copy.deepcopy(self.events)
        events[0]["value"] = 0
        _, _, summary = audit(self.evidence, self.expansion, events)
        self.assertEqual(summary["status"], "evidence_event_mismatch")
        self.assertEqual(summary["event_mismatches"], 1)

    def test_optional_secondary_source_can_be_serialized_in_union_grid(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["decisions"][-1]["secondary_source_url"] = "https://example.org/secondary"
        rows, _, _ = audit(evidence, self.expansion, self.events)
        fields = list(dict.fromkeys(key for row in rows for key in row))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "audit.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader(); writer.writerows(rows)
            self.assertIn("secondary_source_url", path.read_text())


if __name__ == "__main__":
    unittest.main()
