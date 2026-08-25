import unittest
from datetime import date

from src.pipeline.stablecoin_global_market import coverage, normalize


class StablecoinGlobalMarketTests(unittest.TestCase):
    def test_normalizes_usd_valued_pegged_usd_field(self):
        payload = [{"date": "1767225600", "totalCirculating": {"peggedUSD": 99}, "totalCirculatingUSD": {"peggedUSD": 101}}]
        rows = normalize(payload, date(2026, 1, 1), date(2026, 1, 1))
        self.assertEqual(rows[0]["global_peggedusd_circulating_usd"], 101.0)
        self.assertEqual(rows[0]["source_field"], "totalCirculatingUSD.peggedUSD")

    def test_coverage_does_not_impute_missing_days(self):
        rows = [{"date": "2026-01-01"}, {"date": "2026-01-03"}]
        audit = coverage(rows, date(2026, 1, 1), date(2026, 1, 3))
        self.assertEqual(audit["observed_days"], 2)
        self.assertAlmostEqual(audit["coverage_ratio"], 2 / 3)
        self.assertEqual(audit["status"], "review")
