import unittest
from src.pipeline.crypto_h3_supply_event_ledger import build

class Tests(unittest.TestCase):
    def test_exact_events_qualify_and_month_end_candidate_does_not(self):
        spec={"status":"frozen_before_supply_event_collection_and_estimation","market_window":{"start":"2025-01-01","end":"2025-12-31"},"event_selection":{"minimum_impact_share_of_pre_event_circulating_supply":.005}}
        sources={"sources":[{"asset_id":"crypto_arb","source_url":"https://official","first_monthly_post_cliff_date":"2025-04-16","last_monthly_date":"2025-05-16","locked_allocation_tokens":3600,"initial_cliff_share":.25,"remaining_monthly_periods":36},{"asset_id":"crypto_sui","source_url":"https://official"}]}
        market=[{"asset_id":"crypto_arb","date":"2025-04-15","price_usd":"1","market_cap_usd":"10000"},{"asset_id":"crypto_arb","date":"2025-05-15","price_usd":"1","market_cap_usd":"10000"}]
        rows,summary=build(spec,sources,market)
        self.assertEqual(summary["eligible_events"],2); self.assertEqual(rows[-1]["primary_eligible"],0)
        self.assertIn("no_exact_effective_date",rows[-1]["exclusion_reason"])

    def test_official_bnb_burn_uses_market_supply_and_positive_expected_sign(self):
        spec={"status":"frozen_before_supply_event_collection_and_estimation","market_window":{"start":"2025-01-01","end":"2025-12-31"},"event_selection":{"minimum_impact_share_of_pre_event_circulating_supply":.005}}
        sources={"sources":[{"asset_id":"crypto_bnb","events":[{"event_id":"burn","event_date":"2025-10-27","gross_token_impact":100,"source_url":"https://official"}]}]}
        market=[{"asset_id":"crypto_bnb","date":"2025-10-27","price_usd":"2","market_cap_usd":"20000"}]
        rows,summary=build(spec,sources,market)
        self.assertEqual(summary["eligible_assets"],["crypto_bnb"])
        self.assertEqual(rows[0]["expected_return_sign"],"positive")
        self.assertAlmostEqual(rows[0]["impact_share"],.01)

if __name__=="__main__": unittest.main()
