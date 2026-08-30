import unittest
import csv
from pathlib import Path

from src.pipeline.crypto_design_evidence import audit, run, validate_evidence
from src.pipeline.crypto_economic_design import CODES


REGISTRY = {"assets": [{"asset_id":"crypto_x","symbol":"X","universe":"crypto","tier":"market_core"}]}
DESIGN = {"schema_version":1,"as_of":"2026-08-22","status":"provisional","value_accrual_codes":list(CODES),"assets":[{"asset_id":"crypto_x","consensus":"PoS","codes":[0]*10}]}


def evidence(status="verified", value=0):
    return {"schema_version":1,"as_of":"2026-08-22","assets":["crypto_x"],"codes":["VA_BURN"],"decisions":[{"asset_id":"crypto_x","code":"VA_BURN","status":status,"recommended_value":value,"source_url":"https://example.org/rule","source_date":"2026-08-01","date_basis":"published","rationale":"Protocol evidence."}]}


class CryptoDesignEvidenceTests(unittest.TestCase):
    def test_requires_complete_cartesian_tranche(self):
        bad=evidence(); bad["decisions"]=[]
        with self.assertRaisesRegex(ValueError,"exactly one"):
            validate_evidence(bad,DESIGN,REGISTRY)

    def test_pending_decision_cannot_smuggle_value(self):
        with self.assertRaisesRegex(ValueError,"must not recommend"):
            validate_evidence(evidence("pending_review",1),DESIGN,REGISTRY)

    def test_future_source_is_rejected(self):
        bad=evidence(); bad["decisions"][0]["source_date"]="2026-08-23"
        with self.assertRaisesRegex(ValueError,"later"):
            validate_evidence(bad,DESIGN,REGISTRY)

    def test_requires_date_basis(self):
        bad=evidence(); del bad["decisions"][0]["date_basis"]
        with self.assertRaisesRegex(ValueError,"date_basis"):
            validate_evidence(bad,DESIGN,REGISTRY)

    def test_audit_detects_verified_mismatch(self):
        _,summary=audit(evidence("verified",1),DESIGN,REGISTRY)
        self.assertEqual(summary["verified_mismatches"],1)

    def test_repository_run_writes_blind_focused_review(self):
        repo=Path(__file__).resolve().parents[1]
        run(repo)
        with (repo/"data/processed/evidence/crypto_design_evidence_focused_review.csv").open(newline="") as handle:
            rows=list(csv.DictReader(handle))
        self.assertEqual(
            {(row["asset_id"], row["code"]) for row in rows},
            {
                ("crypto_bnb", "VA_MONETARY"),
                ("crypto_bnb", "VA_COLLATERAL"),
            },
        )
        self.assertNotIn("provisional_value", rows[0])
        self.assertNotIn("recommended_value", rows[0])


if __name__ == "__main__": unittest.main()
