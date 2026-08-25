import unittest
from src.pipeline.stablecoin_risk import evaluate,score_block,validate_weights

class StablecoinRiskTests(unittest.TestCase):
    def test_complete_score(self):
        r=score_block({"a":100,"b":50},{"a":50,"b":50})
        self.assertEqual(r["strict_score"],75);self.assertEqual(r["completeness"],1)
    def test_incomplete_withholds_strict_score(self):
        r=score_block({"a":100,"b":None},{"a":50,"b":50})
        self.assertIsNone(r["strict_score"]);self.assertEqual(r["partial_score"],100);self.assertEqual(r["completeness"],.5)
    def test_invalid_weight_total(self):
        with self.assertRaisesRegex(ValueError,"sum to 100"):validate_weights({"a":90})
    def test_evidence_required(self):
        c={"schema_version":1,"methodology_version":"x","weights":{"reserve_quality":{"a":100},"transparency":{"a":100},"redemption_friction":{"a":100}},"assets":[{"asset_id":"x","reserve_quality":{"a":1},"transparency":{"a":1},"redemption_friction":{"a":1}}]}
        with self.assertRaisesRegex(ValueError,"missing evidence"):evaluate(c)

if __name__=="__main__":unittest.main()
