import unittest

from src.pipeline.crypto_monetary import assess,validate


def spec(status="verified",value=1):
    return {"schema_version":1,"as_of":"2026-08-22","activity_window":{"start":"2026-01-01","end":"2026-01-02","minimum_days":2,"median_active_addresses":10,"median_transactions":10},"minimum_tests_to_qualify":2,"assets":[{"asset_id":"crypto_x","monetary_design_status":status,"monetary_design_value":value,"source_url":"https://example.org","source_date":"2025-01-01","date_basis":"published","rationale":"x"}]}


class CryptoMonetaryTests(unittest.TestCase):
    def test_two_independent_tests_required(self):
        s=spec(); s["activity_window"]["minimum_days"]=30
        rows=[{"asset_id":"crypto_x","date":f"2026-01-{d:02d}","active_addresses":"20","transaction_count":"30"} for d in range(1,3)]
        result=assess(s,rows)[0]
        self.assertIsNone(result["recommended_va_monetary"])

    def test_missing_activity_never_becomes_negative(self):
        s=spec(); s["activity_window"]["minimum_days"]=30
        result=assess(s,[])[0]
        self.assertEqual(result["status"],"unresolved_no_negative_inference")

    def test_pending_design_must_be_null(self):
        bad=spec("pending",1); bad["activity_window"]["minimum_days"]=30
        with self.assertRaisesRegex(ValueError,"remain null"): validate(bad)

    def test_complete_below_threshold_and_reviewed_design_can_be_negative(self):
        s=spec("verified",0); s["activity_window"]["minimum_days"]=30; s["activity_window"]["end"]="2026-01-30"
        rows=[{"asset_id":"crypto_x","date":f"2026-01-{d:02d}","active_addresses":"1","transaction_count":"2"} for d in range(1,31)]
        result=assess(s,rows)[0]
        self.assertEqual(result["recommended_va_monetary"],0); self.assertEqual(result["status"],"verified_negative")


if __name__=="__main__": unittest.main()
