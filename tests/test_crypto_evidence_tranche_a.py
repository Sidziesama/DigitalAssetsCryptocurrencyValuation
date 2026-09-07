import unittest

from src.pipeline.crypto_evidence_tranche_a import audit, validate_tranche

REGISTRY = {"schema_version": 1, "as_of": "2026-09-07",
            "assets": [{"asset_id": "crypto_btc", "symbol": "BTC", "universe": "crypto"},
                       {"asset_id": "crypto_eth", "symbol": "ETH", "universe": "crypto"}]}


def design():
    return {"schema_version": 1, "as_of": "2026-09-07", "status": "provisional_pending_targeted_review",
            "value_accrual_codes": ["VA_MONETARY", "VA_GAS", "VA_STAKE", "VA_BURN", "VA_SCARCITY",
                                     "VA_COLLATERAL", "VA_GOV", "VA_PROTOCOL", "VA_UTILITY", "VA_INCENTIVE"],
            "assets": [{"asset_id": "crypto_btc", "consensus": "pow", "codes": [1, 0, 0, 0, 1, 1, 0, 0, 0, 0]},
                       {"asset_id": "crypto_eth", "consensus": "pos", "codes": [1, 1, 1, 1, 0, 1, 0, 1, 1, 0]}]}


def decision(asset, code, status="verified", value=0):
    return {"asset_id": asset, "code": code, "status": status,
            "recommended_value": value if status == "verified" else None,
            "source_url": "https://example.org/spec", "source_date": "2026-09-01",
            "date_basis": "retrieved_as_of", "rationale": "documented mechanism", "verification": "url_confirmed_by_coder"}


def evidence(cases=None, pending_gas=True):
    codes = ["VA_GAS", "VA_STAKE"]
    decisions = []
    for asset in ("crypto_btc", "crypto_eth"):
        for code in codes:
            status = "pending" if (code == "VA_GAS" and asset == "crypto_btc" and pending_gas) else "verified"
            decisions.append(decision(asset, code, status, 1 if code == "VA_STAKE" and asset == "crypto_eth" else 0))
    return {"schema_version": 1, "document_version": "test", "as_of": "2026-09-07", "tranche": "A",
            "tranche_order_rule": "difficulty order fixed in advance",
            "assets": ["crypto_btc", "crypto_eth"], "codes": codes,
            "review_status": "awaiting_independent_blind_review",
            "adjudication_rule": "pending never defaults to zero",
            "consistency_cases": cases if cases is not None else
                [{"case_id": "c1", "assets": ["crypto_btc"], "code": "VA_GAS",
                  "status": "open_requires_adjudication", "precedent": "p", "question": "q", "recommendation": "r"}],
            "decisions": decisions}


class CryptoEvidenceTrancheATests(unittest.TestCase):
    def test_audit_reports_pending_and_mismatches(self):
        rows, worksheet, summary = audit(evidence(), design(), REGISTRY)
        self.assertEqual(summary["decisions"], 4)
        self.assertEqual(summary["pending_decisions"], 1)
        self.assertEqual(summary["verified_decisions"], 3)
        self.assertEqual(summary["provisional_matrix_mismatches"], 1)
        self.assertEqual(summary["mismatch_detail"][0]["asset_id"], "crypto_eth")
        self.assertEqual(len(worksheet), 4)
        self.assertTrue(all(row["reviewer_value"] == "" for row in worksheet))

    def test_blind_worksheet_never_leaks_the_coder_value(self):
        _, worksheet, _ = audit(evidence(), design(), REGISTRY)
        for row in worksheet:
            self.assertNotIn("recommended_value", row)
            self.assertNotIn("rationale", row)

    def test_consistency_case_must_name_a_pending_cell(self):
        with self.assertRaisesRegex(ValueError, "not pending"):
            audit(evidence(pending_gas=False), design(), REGISTRY)

    def test_tranche_label_and_order_rule_are_required(self):
        bad = evidence()
        bad["tranche_order_rule"] = ""
        with self.assertRaisesRegex(ValueError, "tranche-order rule"):
            validate_tranche(bad)


if __name__ == "__main__":
    unittest.main()
