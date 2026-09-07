import unittest

from src.pipeline.crypto_h2_pilot_panel import build, mechanism_state, number, validate_spec


SPEC={
    "schema_version":1,"status":"draft_not_frozen","as_of":"2026-01-08",
    "analysis_window":{"start":"2026-01-01","end":"2026-01-08"},
    "sample":{"market_assets":["crypto_x","crypto_a","crypto_b","crypto_c","crypto_d","crypto_e"],"activity_assets":["crypto_x"],"no_outcome_based_replacement":True},
    "H2":{"primary_status":"candidate_fee_layer_ready_preregistration_freeze_pending","scope_design":{"scope_indicator":"application_protocol_scope","sensitivities":["a","b","c","d"],"pooling_guardrail":"required"},"models":{"market_cap":"x","forward_return":"x","secondary":"x"},"standard_errors":{"primary":"wild-cluster-bootstrap","small_sample_guardrail":"exploratory with only six assets"}},
    "H8":{"status":"five_asset_complete_case_ready_bnb_withheld"},
}


class CryptoH2PilotPanelTests(unittest.TestCase):
    def test_outcome_based_replacement_is_rejected(self):
        bad={**SPEC,"sample":{**SPEC["sample"],"no_outcome_based_replacement":False}}
        with self.assertRaisesRegex(ValueError,"replacement"): validate_spec(bad)

    def test_zero_activity_is_observed_not_missing(self):
        self.assertEqual(number("0",True),0)
        self.assertIsNone(number("0"))

    def test_scope_design_is_required(self):
        bad={**SPEC,"H2":{**SPEC["H2"],"scope_design":{}}}
        with self.assertRaisesRegex(ValueError,"fee-scope design"): validate_spec(bad)

    def test_effective_event_never_backfills(self):
        events=[{"asset_id":"crypto_x","code":"VA_BURN","effective_from":"2026-01-02","value":1}]
        self.assertIsNone(mechanism_state(events,"crypto_x","VA_BURN",__import__("datetime").date(2026,1,1)))
        self.assertEqual(mechanism_state(events,"crypto_x","VA_BURN",__import__("datetime").date(2026,1,2)),1)

    def test_latest_historical_state_applies_after_transition(self):
        events = [
            {"asset_id": "crypto_x", "code": "VA_PROTOCOL", "effective_from": "2025-04-09", "value": 1},
            {"asset_id": "crypto_x", "code": "VA_PROTOCOL", "effective_from": "2026-04-19", "value": 0},
        ]
        date_type = __import__("datetime").date
        self.assertEqual(mechanism_state(events, "crypto_x", "VA_PROTOCOL", date_type(2026, 4, 18)), 1)
        self.assertEqual(mechanism_state(events, "crypto_x", "VA_PROTOCOL", date_type(2026, 4, 19)), 0)

    def test_exact_lag_and_forward_return(self):
        market=[
            {"asset_id":"crypto_x","date":"2026-01-01","price_usd":"100","market_cap_usd":"1000"},
            {"asset_id":"crypto_x","date":"2026-01-02","price_usd":"110","market_cap_usd":"1100"},
            {"asset_id":"crypto_x","date":"2026-01-08","price_usd":"120","market_cap_usd":"1200"},
        ]
        activity=[{"asset_id":"crypto_x","date":"2026-01-01","active_addresses":"10","transaction_count":"20"}]
        events=[
            {"asset_id":"crypto_x","code":"VA_BURN","effective_from":"2025-01-01","value":1},
            {"asset_id":"crypto_x","code":"VA_PROTOCOL","effective_from":"2025-01-01","value":0},
        ]
        rows,summary=build(SPEC,market,activity,events); by_date={row["date"]:row for row in rows}
        self.assertEqual(by_date["2026-01-02"]["active_addresses_lag1"],10)
        self.assertEqual(by_date["2026-01-02"]["application_protocol_scope"],None)
        self.assertIsNotNone(by_date["2026-01-01"]["forward_log_return_7d"])
        self.assertIsNone(by_date["2026-01-02"]["forward_log_return_7d"])
        self.assertEqual(summary["level_eligible_rows"],1)


if __name__=="__main__": unittest.main()
