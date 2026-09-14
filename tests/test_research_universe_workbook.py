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
        self.assertGreater(summary["cell_status"]["verified"], 0)

    def test_pending_cells_carry_no_value(self):
        """Unknown must never become zero; a held cell stays null."""
        data = collect(REPO)
        pending = [(k, v) for k, v in data["cells"].items() if v[1] == "pending"]
        self.assertTrue(pending, "expected held cells from the tranche")
        for key, (value, _status, _url, _date) in pending:
            self.assertIsNone(value, f"{key} is pending but carries a value")

    def test_verified_cells_outrank_provisional_ones(self):
        """A verified decision must override the provisional design matrix."""
        data = collect(REPO)
        verified = {k for k, v in data["cells"].items() if v[1] == "verified"}
        self.assertEqual(len(verified), 60)

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
