import unittest

from src.pipeline.crypto_market_valuation_dashboard import build, render_svg


def profile(index: int) -> dict[str, str]:
    return {
        "asset_id": f"asset_{index}", "symbol": f"A{index}", "architecture_context": "PoS",
        "classification_status": "complete_human_verified",
        "bundle_monetary_store": "0", "bundle_transaction_service_demand": "1" if index == 0 else "0",
        "bundle_security_commitment": "0", "bundle_supply_absorption": "0", "bundle_financial_integration": "0",
        "bundle_control_rights": "0", "bundle_holder_capture": "1" if index == 0 else "0",
        "bundle_subsidized_participation": "0",
    }


class Tests(unittest.TestCase):
    def setUp(self):
        self.spec = {"schema_version": 1, "status": "frozen_before_dashboard_estimation", "document_version": "test", "freeze_date": "2026-01-01", "market_data_end_date": "2025-12-31", "valuation_average_days": 30, "annualization_days": 365, "guardrails": []}
        self.profiles = [profile(i) for i in range(23)]
        self.returns = [{"asset_id": "asset_0", "date": f"2025-01-{day:02d}", "close_usdt": str(100 + day), "realized_volatility_30d_annualized": "0.5" if day == 31 else "", "market_beta_180d_lag1": "", "log_dollar_volume": "10"} for day in range(1, 32)]
        self.risk = [{"asset_id": "asset_0", "market_beta": "1.2", "max_drawdown_log": "-0.4", "mean_log_dollar_volume": "10"}]
        self.valuation = [{"asset_id": "asset_0", "date": "2025-01-31", "market_cap_usd": "1000000", "fees_usd_lag1": "100", "holders_revenue_usd_lag1": "20"}]
        self.advice = {"profiles": [{"asset_id": f"asset_{i}", "closest_economic_comparables": []} for i in range(23)]}

    def test_function_relevance_controls_metric_state(self):
        result = build(self.spec, self.profiles, self.returns, self.risk, self.valuation, self.advice)
        first, second = result["asset_results"][:2]
        self.assertEqual(first["valuation_metrics"]["market_cap_to_annualized_holder_revenue"]["state"], "measured")
        self.assertEqual(second["valuation_metrics"]["market_cap_to_annualized_holder_revenue"]["state"], "not_applicable")
        self.assertIsNone(first["investment_score"])

    def test_missing_is_not_zero(self):
        result = build(self.spec, self.profiles, self.returns, self.risk, [], self.advice)
        metric = result["asset_results"][0]["valuation_metrics"]["market_cap_to_annualized_fees"]
        self.assertEqual(metric["state"], "data_unavailable")
        self.assertIsNone(metric["value"])

    def test_svg_is_accessible(self):
        result = build(self.spec, self.profiles, self.returns, self.risk, self.valuation, self.advice)
        svg = render_svg(result)
        self.assertIn('role="img"', svg)
        self.assertIn("A0", svg)
        self.assertTrue(svg.endswith("</svg>\n"))


if __name__ == "__main__":
    unittest.main()
