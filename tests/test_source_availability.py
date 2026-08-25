import unittest
from src.pipeline.source_availability import build_rows,render_findings

class SourceAvailabilityTests(unittest.TestCase):
    def test_five_metrics_per_asset(self):
        assets=[{"asset_id":"stable_x","universe":"stablecoin","defillama_id":"1"},{"asset_id":"crypto_y","universe":"crypto"}]
        rows=build_rows(assets)
        self.assertEqual(len(rows),10)
        supply=[r for r in rows if r["asset_id"]=="stable_x" and r["metric"]=="circulating_supply_daily"][0]
        self.assertEqual(supply["availability"],"implemented")
        crypto_supply=[r for r in rows if r["asset_id"]=="crypto_y" and r["metric"]=="circulating_supply_daily"][0]
        self.assertEqual(crypto_supply["availability"],"blocked")
        self.assertIn("Daily market capitalization: 2 assets",render_findings(rows))

if __name__=="__main__":unittest.main()
