import unittest

from src.pipeline.h7_readiness import coverage_matrix, join_recent


class H7ReadinessTests(unittest.TestCase):
    def test_exact_day_lag_and_complete_flag(self):
        adoption = [{"asset_id": "x", "date": "2025-08-25", "failure_control": "0", "pilot_observed_supply_share": ".2", "global_peggedusd_supply_share": ".1", "supply_growth_30d": ".1", "absolute_peg_error_bps": "1", "breach_50bps": "0"}]
        chains = [{"asset_id": "x", "date": "2025-08-24", "chain_to_reported_supply_ratio": "1", "material_chain_count_1m_usd": "2", "effective_chain_count": "1.5", "top_chain_share": ".8"}]
        trading = [{"asset_id": "x", "date": "2025-08-24", "volume_to_reported_market_cap": ".5", "log1p_volume_24h_usd": "2"}]
        row = join_recent(adoption, chains, trading, [])[0]
        self.assertEqual(row["effective_chain_count_lag1"], "1.5"); self.assertEqual(row["complete_recent_h7_row"], 1)

    def test_bad_chain_reconciliation_nulls_chain_metrics(self):
        adoption = [{"asset_id": "x", "date": "2025-08-25", "pilot_observed_supply_share": ".2", "global_peggedusd_supply_share": ".1", "supply_growth_30d": ".1", "absolute_peg_error_bps": "1", "breach_50bps": "0"}]
        chains = [{"asset_id": "x", "date": "2025-08-24", "chain_to_reported_supply_ratio": ".5", "material_chain_count_1m_usd": "2", "effective_chain_count": "1.5", "top_chain_share": ".8"}]
        row = join_recent(adoption, chains, [], [])[0]
        self.assertIsNone(row["effective_chain_count_lag1"]); self.assertEqual(row["complete_recent_h7_row"], 0)

    def test_coverage_gate(self):
        row = {metric: "1" for metric in ("global_peggedusd_supply_share", "supply_growth_30d", "material_chain_count_1m_usd_lag1", "effective_chain_count_lag1", "top_chain_share_lag1", "volume_to_reported_market_cap_lag1")}
        row["asset_id"] = "x"; rows = [row]
        rows[0]["complete_recent_h7_row"] = 1
        self.assertTrue(all(row["gate"] == "pass" for row in coverage_matrix(rows)))


if __name__ == "__main__": unittest.main()
