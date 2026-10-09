import unittest

from src.pipeline.crypto_risk_verified_visual import build


class Tests(unittest.TestCase):
    def test_builds_accessible_sorted_svg(self):
        rows = [
            {"estimable": "1", "predictor": "bundle_monetary_store", "outcome": "market_beta", "permutation_p_two_sided": "0.08", "benjamini_hochberg_q": "0.2"},
            {"estimable": "1", "predictor": "raw_function_breadth", "outcome": "max_drawdown_log", "permutation_p_two_sided": "0.01", "benjamini_hochberg_q": "0.1"}
        ]
        svg = build(rows)
        self.assertIn('role="img"', svg)
        self.assertLess(svg.index("Raw Function Breadth"), svg.index("Monetary Store"))
        self.assertTrue(svg.endswith("</svg>\n"))


if __name__ == "__main__":
    unittest.main()
