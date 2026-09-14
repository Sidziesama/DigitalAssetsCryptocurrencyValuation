import re
import unittest
from pathlib import Path

from src.pipeline.classification_status import CODES, DEFINITIONS, build

REPO = Path(__file__).resolve().parents[1]
DOCS = ["CLAUDE.md", "PROJECT_PLAN.md", "README.md", "research/manuscript/main.tex"]


class ClassificationStatusTests(unittest.TestCase):
    def setUp(self):
        self.summary = build(REPO)

    def test_counts_reconcile_to_the_full_grid(self):
        self.assertEqual(sum(self.summary["counts"].values()), self.summary["total_cells"])
        self.assertEqual(self.summary["total_cells"], self.summary["assets"] * len(CODES))

    def test_reviewed_is_a_strict_subset_of_evidence_backed(self):
        s = self.summary
        self.assertEqual(s["evidence_backed"], s["counts"]["sourced"] + s["counts"]["reviewed"])
        self.assertLessEqual(s["counts"]["reviewed"], s["evidence_backed"])

    def test_review_only_counts_completed_worksheets(self):
        """A reliability claim requires a completed blind worksheet on disk."""
        worksheet = REPO / "review_inputs/crypto_h2_expansion_blind_review.csv"
        if not worksheet.exists():
            self.assertEqual(self.summary["counts"]["reviewed"], 0)
        else:
            self.assertGreater(self.summary["counts"]["reviewed"], 0)

    def test_the_core_is_not_counted_as_reviewed(self):
        """The six-asset core is sourced. Claiming otherwise overstates reliability."""
        self.assertEqual(self.summary["core_cells_sourced_not_reviewed"], 60)
        self.assertNotIn("crypto_btc", self.summary["reviewed_scope"]["assets"])

    def test_definitions_are_published_with_the_counts(self):
        self.assertEqual(set(self.summary["counts"]), set(DEFINITIONS))

    def test_no_document_claims_the_core_was_blind_reviewed(self):
        """Guards the specific error this module exists to prevent."""
        banned = re.compile(
            r"(six-asset core|sixty of sixty|60 of 60)[^.]{0,120}(blind[- ]review|reconciled with a blind|kappa)",
            re.IGNORECASE)
        for name in DOCS:
            path = REPO / name
            if not path.exists():
                continue
            hit = banned.search(path.read_text(encoding="utf-8"))
            self.assertIsNone(hit, f"{name} appears to attribute blind review to the core: {hit.group(0) if hit else ''}")

    def test_headline_counts_in_docs_match_the_computed_ones(self):
        backed, reviewed = self.summary["evidence_backed"], self.summary["counts"]["reviewed"]
        for name in ("CLAUDE.md", "PROJECT_PLAN.md", "README.md"):
            text = (REPO / name).read_text(encoding="utf-8")
            self.assertIn(str(backed), text, f"{name} does not state the evidence-backed count")
            self.assertRegex(text, rf"\b{reviewed}\b", f"{name} does not state the reviewed count")


if __name__ == "__main__":
    unittest.main()
