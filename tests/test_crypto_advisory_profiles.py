import unittest

from src.pipeline.crypto_advisory_profiles import build


class Tests(unittest.TestCase):
    def test_profiles_have_actions_but_no_investment_scores(self):
        rows=[]
        for i in range(23):
            rows.append({"asset_id":f"a{i}","symbol":f"A{i}","architecture_context":"test","classification_status":"complete_human_verified","va_scarcity":"0","bundle_monetary_store":"1" if i<2 else "0","bundle_transaction_service_demand":"0","bundle_security_commitment":"0","bundle_supply_absorption":"0","bundle_financial_integration":"0","bundle_control_rights":"1" if i==0 else "0","bundle_holder_capture":"0","bundle_subsidized_participation":"0"})
        result=build(rows)
        self.assertEqual(result["assets"],23)
        self.assertIsNone(result["profiles"][0]["investment_score"])
        self.assertIn("must not be described", " ".join(result["profiles"][0]["key_cautions"]))
        self.assertEqual(result["profiles"][0]["closest_economic_comparables"][0]["symbol"],"A1")


if __name__=="__main__": unittest.main()
