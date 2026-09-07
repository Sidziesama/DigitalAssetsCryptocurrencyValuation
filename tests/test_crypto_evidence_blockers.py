import unittest

from src.pipeline.crypto_evidence_blockers import build


def manifest():
    return {"blockers": []}


class CryptoEvidenceBlockersTests(unittest.TestCase):
    def test_manifest_reconciles_exact_unresolved_decisions(self):
        decisions = [
            {"asset_id": row["asset_id"], "code": row["code"], "status": row["current_status"]}
            for row in manifest()["blockers"]
        ]
        self.assertEqual(build(manifest(), decisions)["open_blockers"], 0)

    def test_manifest_rejects_stale_resolution(self):
        decisions = [{"asset_id":"crypto_bnb","code":"VA_MONETARY","status":"pending_quantitative_behavior"}]
        with self.assertRaisesRegex(ValueError, "no longer reconciles"):
            build(manifest(), decisions)


if __name__ == "__main__":
    unittest.main()
