import unittest

from src.pipeline.crypto_h8_evidence_plan import EXPECTED_CODES, build, merge_evidence, validate, validate_evidence


def spec():
    rule={"positive_rule":"Positive.","negative_rule":"Negative.","required_evidence":"Primary."}
    return {"schema_version":1,"assets":[f"crypto_{i}" for i in range(6)],"codes":{code:dict(rule) for code in EXPECTED_CODES},"review_rule":"Blind review."}


class CryptoH8EvidencePlanTests(unittest.TestCase):
    def test_builds_blind_complete_grid(self):
        _,rows,summary=build(spec())
        self.assertEqual(len(rows),36); self.assertEqual(summary["pending_decisions"],36)
        self.assertNotIn("provisional_value",rows[0]); self.assertNotIn("recommended_value",rows[0])

    def test_rejects_incomplete_code_rule(self):
        bad=spec(); del bad["codes"]["VA_GAS"]["negative_rule"]
        with self.assertRaisesRegex(ValueError,"incomplete"): validate(bad)

    def test_pending_evidence_cannot_smuggle_value(self):
        plan=spec(); evidence={"schema_version":1,"as_of":"2026-01-02","assets":plan["assets"],"codes":["VA_GAS"],"decisions":[]}
        for asset in plan["assets"]:
            evidence["decisions"].append({"asset_id":asset,"code":"VA_GAS","status":"pending","recommended_value":1,"source_url":"https://example.org","source_date":"2026-01-01","date_basis":"published","rationale":"Pending."})
        with self.assertRaisesRegex(ValueError,"remain null"): validate_evidence(evidence,plan)

    def test_merge_rejects_overlapping_decisions(self):
        plan=spec(); tranche={"schema_version":1,"as_of":"2026-01-02","assets":plan["assets"],"codes":["VA_GAS"],"decisions":[]}
        for asset in plan["assets"]:
            tranche["decisions"].append({"asset_id":asset,"code":"VA_GAS","status":"pending","recommended_value":None,"source_url":"https://example.org","source_date":"2026-01-01","date_basis":"published","rationale":"Pending."})
        with self.assertRaisesRegex(ValueError,"duplicate H8 evidence decision"):
            merge_evidence(plan,[tranche,tranche])

    def test_complete_evidence_produces_empty_review(self):
        plan=spec(); evidence={"schema_version":1,"as_of":"2026-01-02","assets":plan["assets"],"codes":list(EXPECTED_CODES),"decisions":[]}
        for asset in plan["assets"]:
            for code in EXPECTED_CODES:
                evidence["decisions"].append({"asset_id":asset,"code":code,"status":"verified","recommended_value":0,"source_url":"https://example.org","source_date":"2026-01-01","date_basis":"published","rationale":"Verified."})
        _,review,summary=build(plan,evidence)
        self.assertEqual(review,[]); self.assertEqual(summary["status"],"six_code_evidence_complete")


if __name__=="__main__": unittest.main()
