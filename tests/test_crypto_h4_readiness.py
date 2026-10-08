import unittest

from src.pipeline.crypto_h4_readiness import build, evidence_values


class CryptoH4ReadinessTests(unittest.TestCase):
    def test_static_stake_classification_does_not_release_estimation(self):
        decisions = {"decisions": [
            {"asset_id": f"a{i}", "code": "VA_STAKE", "status": "verified", "recommended_value": int(i < 3)}
            for i in range(6)
        ]}
        verified = evidence_values(decisions)
        plan = {"schema_version": 1, "hypothesis": "H4", "universe_policy":"fixed_existing_six_assets_no_expansion", "assets": [
            {"asset_id": f"a{i}", "va_stake": int(i < 3), "official_source_url": "https://example.org",
             "historical_staked_supply_status": "not_implemented", "staking_system": "x", "comparability_group": "x"}
            for i in range(6)
        ]}
        market = [{"asset_id": f"a{i}", "date": "2026-01-01", "volume_24h_usd": "1", "market_cap_usd": "2"} for i in range(6)]
        result = build(plan, verified, market)
        self.assertFalse(result["identification_ready"])
        self.assertEqual(result["positive_assets_with_historical_staking"], 0)
        self.assertEqual(result["market_proxy_assets"], 6)

    def test_three_positive_histories_release_readiness(self):
        decisions = {"decisions": [
            {"asset_id": f"a{i}", "code": "VA_STAKE", "status": "verified", "recommended_value": int(i < 3)}
            for i in range(6)
        ]}
        plan = {"schema_version": 1, "hypothesis": "H4", "universe_policy":"fixed_existing_six_assets_no_expansion", "assets": [
            {"asset_id": f"a{i}", "va_stake": int(i < 3), "official_source_url": "https://example.org",
             "historical_staked_supply_status": "implemented" if i < 3 else "structural_zero",
             "staking_system": "x", "comparability_group": "x"}
            for i in range(6)
        ]}
        self.assertTrue(build(plan, evidence_values(decisions), [])["identification_ready"])

    def test_plan_must_reconcile_verified_values(self):
        with self.assertRaisesRegex(ValueError, "exact six-asset"):
            build({"schema_version": 1, "hypothesis": "H4", "universe_policy":"fixed_existing_six_assets_no_expansion", "assets": []}, {"a": 1}, [])

    def test_partial_component_is_reported_but_does_not_release_readiness(self):
        decisions = {"decisions": [
            {"asset_id": f"a{i}", "code": "VA_STAKE", "status": "verified", "recommended_value": int(i < 3)}
            for i in range(6)]}
        plan = {"schema_version":1,"hypothesis":"H4","universe_policy":"fixed_existing_six_assets_no_expansion","assets":[
            {"asset_id":f"a{i}","va_stake":int(i<3),"official_source_url":"https://example.org",
             "historical_staked_supply_status":"not_implemented","staking_system":"x","comparability_group":"x"}
            for i in range(6)]}
        result = build(plan, evidence_values(decisions), [], [{"asset_id":"a0","observed_days":90}])
        self.assertEqual(result["positive_assets_with_partial_component_history"], 1)
        self.assertFalse(result["identification_ready"])

    def test_short_unblocking_component_does_not_meet_history_rule(self):
        decisions={"decisions":[{"asset_id":f"a{i}","code":"VA_STAKE","status":"verified","recommended_value":int(i<3)} for i in range(6)]}
        plan={"schema_version":1,"hypothesis":"H4","universe_policy":"fixed_existing_six_assets_no_expansion","minimum_history_days":365,"assets":[{"asset_id":f"a{i}","va_stake":int(i<3),"official_source_url":"https://example.org","historical_staked_supply_status":"not_implemented","staking_system":"x","comparability_group":"x"} for i in range(6)]}
        result=build(plan,evidence_values(decisions),[],[{"asset_id":"a0","observed_days":90,"unblocks_h4":True}])
        self.assertEqual(result["positive_assets_with_historical_staking"],0)
        self.assertEqual(result["audit"][0]["staking_history_days"],90)


if __name__ == "__main__":
    unittest.main()
