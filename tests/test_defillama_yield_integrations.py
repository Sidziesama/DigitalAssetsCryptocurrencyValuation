import unittest

from src.pipeline.defillama_yield_integrations import match_pools, symbol_components


class DefiLlamaYieldIntegrationTests(unittest.TestCase):
    def test_exact_components_avoid_substring_false_positive(self):
        self.assertIn("USDC", symbol_components("WETH-USDC"))
        self.assertNotIn("USDC", symbol_components("AUSDC-WETH"))

    def test_match_and_distinct_project_summary(self):
        assets = [{"asset_id": "stable_usdc", "symbol": "USDC"}]
        pools = [
            {"pool": "1", "project": "aave", "chain": "Ethereum", "symbol": "USDC", "tvlUsd": 10, "stablecoin": True},
            {"pool": "2", "project": "aave", "chain": "Base", "symbol": "WETH-USDC", "tvlUsd": 20, "stablecoin": False},
            {"pool": "3", "project": "other", "chain": "Base", "symbol": "AUSDC-WETH", "tvlUsd": 30, "stablecoin": False},
        ]
        matches, summaries = match_pools(assets, pools, "2026-01-01T00:00:00+00:00")
        self.assertEqual(len(matches), 2)
        self.assertEqual(summaries[0]["yield_project_count"], 1)
        self.assertEqual(summaries[0]["yield_chain_count"], 2)
        self.assertEqual(summaries[0]["gross_matched_pool_tvl_usd"], 30)


if __name__ == "__main__":
    unittest.main()
