import unittest
from datetime import date

from src.pipeline.stablecoin_supply import coverage, normalize


class StablecoinSupplyTests(unittest.TestCase):
    def test_normalize_filters_range(self):
        p={"tokens":[{"date":0,"circulating":{"peggedUSD":1}},{"date":86400,"circulating":{"peggedUSD":2}}]}
        self.assertEqual(normalize("stable_x",p,date(1970,1,2),date(1970,1,2))[0]["circulating_peg_usd"],2)

    def test_unsupported_is_explicit(self):
        r=coverage({"asset_id":"stable_gold"},[],date(2020,1,1),date(2020,1,2))
        self.assertEqual(r["status"],"unsupported")

    def test_active_coverage_pass(self):
        a={"asset_id":"stable_x","defillama_id":"1"};rows=[{"date":"2020-01-01"},{"date":"2020-01-02"}]
        self.assertEqual(coverage(a,rows,date(2019,1,1),date(2020,1,2))["status"],"pass")


if __name__=="__main__":unittest.main()
