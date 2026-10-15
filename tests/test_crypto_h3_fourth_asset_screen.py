import unittest

from src.pipeline.crypto_h3_fourth_asset_screen import validate


class Tests(unittest.TestCase):
    def base(self):
        return {"schema_version":1,"screen_date":"2026-10-15","hypothesis":"H3","universe_policy":"existing_active_assets_only","minimum_materiality_share":0.005,"outcome_data_prohibited":True,"candidates":[{"asset_id":"x","official_source_url":"https://example.com","exact_event_date_available":False,"materiality_share":None,"decision":"not_eligible_exact_date_and_amount_missing"}]}

    def test_no_candidate_is_valid_screen_result(self):
        self.assertEqual(validate(self.base())["eligible_assets"],[])

    def test_outcome_fields_are_rejected(self):
        spec=self.base(); spec["candidates"][0]["return"]=0.2
        with self.assertRaises(ValueError): validate(spec)

    def test_eligible_candidate_must_meet_threshold(self):
        spec=self.base(); row=spec["candidates"][0]; row.update({"exact_event_date_available":True,"materiality_share":0.004,"decision":"eligible_for_preregistered_addition"})
        with self.assertRaises(ValueError): validate(spec)


if __name__=="__main__": unittest.main()
