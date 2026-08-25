import unittest

from src.pipeline.binance_stablecoin_depth import analyze, select_pairs, transform_book


class BinanceStablecoinDepthTests(unittest.TestCase):
    def test_pair_selection_prefers_target_as_base(self):
        assets = [{"asset_id": "usdc", "symbol": "USDC"}]
        info = {"symbols": [
            {"symbol": "FDUSDUSDC", "baseAsset": "FDUSD", "quoteAsset": "USDC", "status": "TRADING"},
            {"symbol": "USDCUSDT", "baseAsset": "USDC", "quoteAsset": "USDT", "status": "TRADING"},
        ]}
        resolved, _ = select_pairs(assets, info)
        self.assertEqual(resolved["usdc"]["pair"], "USDCUSDT")
        self.assertTrue(resolved["usdc"]["target_is_base"])

    def test_quote_target_book_is_inverted(self):
        bids, asks = transform_book({"bids": [["0.99", "100"]], "asks": [["1.01", "200"]]}, False)
        self.assertAlmostEqual(bids[0][0], 1 / 1.01)
        self.assertAlmostEqual(bids[0][1], 202)
        self.assertAlmostEqual(asks[0][0], 1 / .99)

    def test_spread_depth_and_fully_filled_impact(self):
        payload = {"bids": [["0.999", "2000000"]], "asks": [["1.001", "2000000"]]}
        row = analyze(payload, True)
        self.assertAlmostEqual(row["quoted_spread_bps"], 20)
        self.assertGreater(row["ask_depth_25bps_anchor"], 1_000_000)
        self.assertIsNotNone(row["buy_impact_1000k_bps"])

    def test_insufficient_depth_withholds_impact(self):
        row = analyze({"bids": [["0.999", "1"]], "asks": [["1.001", "1"]]}, True)
        self.assertIsNone(row["buy_impact_100k_bps"])
        self.assertLess(row["buy_fill_100k"], 1)


if __name__ == "__main__":
    unittest.main()
