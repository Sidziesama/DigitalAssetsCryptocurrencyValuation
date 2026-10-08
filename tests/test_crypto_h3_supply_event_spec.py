import json, unittest
from pathlib import Path

REPO=Path(__file__).resolve().parents[1]

class Tests(unittest.TestCase):
    def test_frozen_h3_event_spec_has_required_guardrails(self):
        spec=json.loads((REPO/"config/crypto_h3_supply_event_study.json").read_text())
        self.assertEqual(spec["status"],"frozen_before_supply_event_collection_and_estimation")
        self.assertEqual(spec["hypothesis"],"H3")
        self.assertEqual(spec["event_selection"]["minimum_impact_share_of_pre_event_circulating_supply"],.005)
        self.assertIn("event_inferred_from_price",spec["event_selection"]["excluded_types"])
        self.assertEqual(spec["estimation"]["primary_event_window_trading_days"],[-1,1])
        self.assertEqual(spec["estimation"]["monte_carlo_draws"],100000)
        self.assertTrue(spec["contamination"]["exclude_when_same_asset_has_another_supply_event"])

if __name__=="__main__": unittest.main()
