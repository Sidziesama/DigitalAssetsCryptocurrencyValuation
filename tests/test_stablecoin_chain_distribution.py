import unittest

from src.pipeline.stablecoin_chain_distribution import chain_observations, distribution_metrics


class StablecoinChainDistributionTests(unittest.TestCase):
    def test_chain_metrics_and_reconciliation(self):
        payload = {"chainBalances": {"A": {"tokens": [{"date": 0, "circulating": {"peggedUSD": 75}}]}, "B": {"tokens": [{"date": 0, "circulating": {"peggedUSD": 25}}]}}}
        by_date = chain_observations("x", payload); row = distribution_metrics("x", by_date, {("x", "1970-01-01"): 100})[0]
        self.assertEqual(row["active_chain_count"], 2); self.assertEqual(row["chain_to_reported_supply_ratio"], 1)
        self.assertEqual(row["chain_hhi"], .625); self.assertEqual(row["top_chain"], "A")

    def test_invalid_and_negative_values_are_ignored(self):
        payload = {"chainBalances": {"A": {"tokens": [{"date": 0, "circulating": {"peggedUSD": -1}}]}}}
        self.assertEqual(chain_observations("x", payload), {})


if __name__ == "__main__": unittest.main()
