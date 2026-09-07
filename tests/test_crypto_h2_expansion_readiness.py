import unittest

from src.pipeline.crypto_h2_expansion_readiness import build


class CryptoH2ExpansionReadinessTests(unittest.TestCase):
    def test_candidate_requires_all_three_evidence_gates(self):
        candidates = [f"asset_{index}" for index in range(5)]
        config = {
            "analysis_window": {"start": "2025-08-26", "end": "2026-08-21"},
            "expansion_assets": candidates,
            "requirements": {
                "market_provider": "coinpaprika",
                "market_status": "pass",
                "required_mechanism_codes": ["VA_BURN", "VA_PROTOCOL"],
                "selection_uses_model_outcomes": False,
            },
        }
        market = [
            {"asset_id": asset, "provider": "coinpaprika", "status": "pass", "start_date": "2025-08-25", "end_date": "2026-08-22"}
            for asset in candidates
        ]
        fees = [{"asset_id": asset, "fees_usd_days": "362", "expected_days": "362"} for asset in candidates]
        events = [
            {"asset_id": asset, "code": code, "effective_from": "2025-01-01"}
            for asset in candidates
            for code in ("VA_BURN", "VA_PROTOCOL")
        ]
        rows, summary = build(config, market, fees, events)
        self.assertEqual(summary["status"], "expansion_ready")
        self.assertTrue(all(row["eligible"] for row in rows))

        fees[0]["fees_usd_days"] = "361"
        _, blocked = build(config, market, fees, events)
        self.assertEqual(blocked["status"], "expansion_blocked")


if __name__ == "__main__":
    unittest.main()
