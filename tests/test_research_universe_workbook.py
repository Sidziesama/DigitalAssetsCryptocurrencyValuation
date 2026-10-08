import unittest
from pathlib import Path

from src.pipeline.research_universe_workbook import CODES, STATUS, build, collect

REPO = Path(__file__).resolve().parents[1]


class ResearchUniverseWorkbookTests(unittest.TestCase):
    def test_every_crypto_cell_has_a_status(self):
        data = collect(REPO)
        registry = [a for a in data["registry"]["assets"] if a["universe"] == "crypto"]
        for asset in registry:
            for code in CODES:
                self.assertIn((asset["asset_id"], code), data["cells"], f"{asset['asset_id']} {code}")

    def test_cell_statuses_reconcile_to_the_full_grid(self):
        _, summary = build(REPO)
        self.assertEqual(sum(summary["cell_status"].values()), summary["cells"])
        self.assertEqual(summary["cells"], summary["crypto_assets"] * len(CODES))
        self.assertGreater(summary["cell_status"]["sourced"], 0)
        self.assertGreater(summary["cell_status"]["reviewed"], 0)

    def test_pending_cells_carry_no_value(self):
        """Unknown must never become zero; a held cell stays null."""
        data = collect(REPO)
        pending = [(k, v) for k, v in data["cells"].items() if v[1] == "pending"]
        for key, (value, _status, _url, _date) in pending:
            self.assertIsNone(value, f"{key} is pending but carries a value")

    def test_evidence_outranks_the_provisional_matrix(self):
        """A sourced or reviewed decision must override the provisional design matrix.

        The expected count comes from the canonical status module, not a literal, so
        closing a documentation gap does not break an unrelated test.
        """
        from src.pipeline.classification_status import build as status_build
        data = collect(REPO)
        backed = {k for k, v in data["cells"].items() if v[1] in ("sourced", "reviewed")}
        self.assertEqual(len(backed), status_build(REPO)["evidence_backed"])
        self.assertGreater(len(backed), 0)

    def test_workbook_agrees_with_the_canonical_status_module(self):
        """The workbook must not invent its own counts."""
        from src.pipeline.classification_status import build as status_build
        _, summary = build(REPO)
        canonical = status_build(REPO)
        self.assertEqual(summary["cell_status"], canonical["counts"])

    def test_reviewed_cells_are_only_the_blind_reviewed_set(self):
        data = collect(REPO)
        reviewed = {a for (a, _c), v in data["cells"].items() if v[1] == "reviewed"}
        self.assertEqual(reviewed, {"crypto_sol", "crypto_avax", "crypto_trx", "crypto_xrp", "crypto_ada"})
        self.assertNotIn("crypto_btc", reviewed)

    def test_workbook_has_the_expected_sheets(self):
        _, summary = build(REPO)
        for sheet in ("README", "Universe", "economic_design", "Codebook", "Adjudications", "Evidence_sources"):
            self.assertIn(sheet, summary["sheets"])

    def test_every_status_has_a_legend_entry(self):
        data = collect(REPO)
        used = {v[1] for v in data["cells"].values()}
        self.assertTrue(used <= set(STATUS), used - set(STATUS))


if __name__ == "__main__":
    unittest.main()
