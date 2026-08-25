import unittest

from src.pipeline.stablecoin_usage_panel import build_panel, summarize


class StablecoinUsagePanelTests(unittest.TestCase):
    def test_exact_lag_and_sample_restriction(self):
        adoption = [
            {"asset_id": "stable_usdc", "date": "2026-01-02", "global_peggedusd_supply_share": ".2", "breach_50bps": "0"},
            {"asset_id": "stable_other", "date": "2026-01-02", "global_peggedusd_supply_share": ".1", "breach_50bps": "0"},
        ]
        usage = [{"asset_id": "stable_usdc", "date": "2026-01-01", "active_addresses": "10", "ledger_transaction_count": "20", "token_transfer_count": "30"}]
        rows = build_panel(adoption, usage, {"stable_usdc"})
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["usage_date_lag1"], "2026-01-01")
        self.assertEqual(rows[0]["complete_usage_row"], 1)

    def test_missing_exact_lag_stays_null(self):
        adoption = [{"asset_id": "stable_usdc", "date": "2026-01-03", "global_peggedusd_supply_share": ".2", "breach_50bps": "0"}]
        usage = [{"asset_id": "stable_usdc", "date": "2026-01-01", "active_addresses": "10", "ledger_transaction_count": "20", "token_transfer_count": "30"}]
        row = build_panel(adoption, usage, {"stable_usdc"})[0]
        self.assertIsNone(row["active_addresses_lag1"])
        self.assertEqual(row["complete_usage_row"], 0)

    def test_summary_preserves_exploratory_role(self):
        summary = summarize([])
        self.assertEqual(summary["analysis_role"], "exploratory_usage_subsample")


if __name__ == "__main__":
    unittest.main()
