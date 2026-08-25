import unittest

from src.pipeline.preregistration import validate


def valid_spec():
    return {"schema_version": 1, "document_version": "x", "status": "draft_not_frozen", "scope": "x", "analysis_window": {}, "sample": {"failure_controls_excluded_primary": ["stable_ustc"], "exclude_reference_assets": ["stable_paxg"], "h7_exploratory_usage_assets": ["stable_usdt", "stable_usdc", "stable_dai", "stable_tusd"], "h7_usage_scope_rule": "exploratory only"}, "peg_measurement": {"primary_recovery_bps": 25, "primary_breach_bps": 50}, "hypotheses": {"H5": {}, "H6": {}, "H7": {}}, "outcomes": {}, "covariates": {"design_effective_date_rule": "evidence/effective date only"}, "models": {}, "missing_data": {"no_silent_imputation": True}, "readiness_gates": {}, "current_readiness": {}}


class PreregistrationTests(unittest.TestCase):
    def test_valid(self): validate(valid_spec())
    def test_recovery_must_be_narrower(self):
        spec = valid_spec(); spec["peg_measurement"]["primary_recovery_bps"] = 50
        with self.assertRaises(ValueError): validate(spec)
    def test_no_silent_imputation_is_mandatory(self):
        spec = valid_spec(); spec["missing_data"]["no_silent_imputation"] = False
        with self.assertRaises(ValueError): validate(spec)
    def test_usage_subsample_cannot_change(self):
        spec = valid_spec(); spec["sample"]["h7_exploratory_usage_assets"].append("stable_other")
        with self.assertRaises(ValueError): validate(spec)


if __name__ == "__main__": unittest.main()
