import unittest
from datetime import date

from src.pipeline.llama_history import batches, chart_url, coverage, nearest_utc_day, normalize


ASSETS=[{"asset_id":"crypto_btc","coingecko_id":"bitcoin"},{"asset_id":"crypto_eth","coingecko_id":"ethereum"}]


class LlamaHistoryTests(unittest.TestCase):
    def test_batching(self):
        self.assertEqual([len(x) for x in batches(ASSETS,1)],[1,1])

    def test_chart_url(self):
        url=chart_url("https://coins.llama.fi",ASSETS[:1],date(2019,1,1),date(2019,1,2))
        self.assertIn("coingecko:bitcoin",url)
        self.assertIn("span=2",url)

    def test_chart_url_rejects_multiple_coins(self):
        with self.assertRaisesRegex(ValueError,"one coin"):
            chart_url("https://coins.llama.fi",ASSETS,date(2019,1,1),date(2019,1,2))

    def test_normalize(self):
        payload={"coins":{"coingecko:bitcoin":{"prices":[{"timestamp":0,"price":1.0},{"timestamp":1,"price":2.0}]}}}
        rows=normalize(payload,ASSETS)
        self.assertEqual(rows,[{"asset_id":"crypto_btc","date":"1970-01-01","price_usd":2.0,"provider":"defillama"}])

    def test_near_midnight_rounds_to_intended_utc_day(self):
        self.assertEqual(nearest_utc_day(86400-30),"1970-01-02")
        self.assertEqual(nearest_utc_day(86400+30),"1970-01-02")

    def test_active_window_coverage(self):
        rows=[{"date":"2026-01-02","price_usd":1},{"date":"2026-01-03","price_usd":1}]
        result=coverage("x",rows,date(2026,1,1),date(2026,1,3))
        self.assertEqual(result["full_window_coverage_ratio"],2/3)
        self.assertEqual(result["active_window_coverage_ratio"],1)
        self.assertEqual(result["status"],"pass")


if __name__=="__main__":unittest.main()
