import unittest

from src.pipeline.crypto_evidence_blockers import build


def manifest():
    return {
        "blockers": [
            {
                "asset_id": "crypto_bnb",
                "code": code,
                "current_status": status,
                "required_evidence": "required",
                "free_source_audit": "audited",
                "resolution_rule": "retain null",
                "acceptable_next_actions": ["retain_null_and_exclude_from_h8"],
            }
            for code, status in (
                ("VA_MONETARY", "pending_quantitative_behavior"),
                ("VA_COLLATERAL", "pending_quantitative_threshold"),
            )
        ]
    }


class CryptoEvidenceBlockersTests(unittest.TestCase):
    def test_manifest_reconciles_exact_unresolved_decisions(self):
        decisions = [
            {"asset_id": row["asset_id"], "code": row["code"], "status": row["current_status"]}
            for row in manifest()["blockers"]
        ]
        self.assertEqual(build(manifest(), decisions)["open_blockers"], 2)

    def test_manifest_rejects_stale_resolution(self):
        decisions = [
            {"asset_id": "crypto_bnb", "code": "VA_MONETARY", "status": "verified"},
            {"asset_id": "crypto_bnb", "code": "VA_COLLATERAL", "status": "pending_quantitative_threshold"},
        ]
        with self.assertRaisesRegex(ValueError, "no longer reconciles"):
            build(manifest(), decisions)


if __name__ == "__main__":
    unittest.main()
