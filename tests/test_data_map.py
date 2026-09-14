import unittest
from pathlib import Path

from src.pipeline.data_map import PHASES, build, classify, render

REPO = Path(__file__).resolve().parents[1]


class DataMapTests(unittest.TestCase):
    def test_every_processed_file_is_catalogued_with_a_writer(self):
        rows, summary = build(REPO)
        self.assertGreater(summary["files"], 100)
        self.assertEqual(summary["orphans"], [], "a processed file has no producer; it is stale")
        self.assertEqual(set(summary["by_phase"]), set(PHASES))

    def test_phases_are_populated(self):
        _, summary = build(REPO)
        for phase in ("00_foundation", "01_classification", "02_valuation", "03_risk"):
            self.assertGreater(summary["by_phase"][phase], 0, phase)

    def test_classify_detects_writes_and_reads(self):
        self.assertEqual(classify("x.csv", 'out = repo / "d"\nwrite_rows(out / "x.csv", rows)'), "writes")
        self.assertEqual(classify("x.csv", 'rows = read_csv(repo / "d" / "x.csv")'), "reads")

    def test_render_includes_a_flowchart_and_every_phase_heading(self):
        rows, summary = build(REPO)
        text = render(rows, summary)
        self.assertIn("```mermaid", text)
        for title, _ in PHASES.values():
            self.assertIn(title, text)


if __name__ == "__main__":
    unittest.main()
