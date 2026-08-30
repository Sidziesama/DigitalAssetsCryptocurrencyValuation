import unittest

from src.pipeline.crypto_h2_h8_readiness import build


class CryptoH2H8ReadinessTests(unittest.TestCase):
    def test_h2_can_be_ready_while_h8_is_withheld(self):
        rows = [
            {"asset_id":"crypto_x","code":"VA_BURN","status":"verified","recommended_value":0},
            {"asset_id":"crypto_x","code":"VA_PROTOCOL","status":"verified","recommended_value":1},
        ]
        panel, summary = build(rows, ["crypto_x"])
        self.assertEqual(panel[0]["h2_active_capture"], 1)
        self.assertEqual(panel[0]["h2_design_ready"], 1)
        self.assertIsNone(panel[0]["h8_value_accrual_breadth"])
        self.assertEqual(summary["h8_design_ready_assets"], 0)

    def test_pending_h2_component_withholds_capture(self):
        rows = [
            {"asset_id":"crypto_x","code":"VA_BURN","status":"verified","recommended_value":1},
            {"asset_id":"crypto_x","code":"VA_PROTOCOL","status":"pending","recommended_value":None},
        ]
        panel, _ = build(rows, ["crypto_x"])
        self.assertIsNone(panel[0]["h2_active_capture"])
        self.assertEqual(panel[0]["h2_design_ready"], 0)

    def test_complete_ten_code_evidence_releases_h8_breadth(self):
        from src.pipeline.crypto_economic_design import CODES

        rows = [
            {
                "asset_id": "crypto_x",
                "code": code,
                "status": "verified",
                "recommended_value": int(code in {"VA_BURN", "VA_PROTOCOL"}),
            }
            for code in CODES
        ]
        panel, summary = build(rows, ["crypto_x"])
        self.assertEqual(panel[0]["h8_value_accrual_breadth"], 2)
        self.assertEqual(summary["status"], "h2_h8_pilot_design_ready")

    def test_duplicate_evidence_is_rejected(self):
        row = {
            "asset_id": "crypto_x",
            "code": "VA_BURN",
            "status": "verified",
            "recommended_value": 1,
        }
        with self.assertRaisesRegex(ValueError, "duplicate"):
            build([row, row], ["crypto_x"])


if __name__ == "__main__":
    unittest.main()
