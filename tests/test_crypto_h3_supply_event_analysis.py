import unittest
from src.pipeline.crypto_h3_supply_event_analysis import chart, exact_asset_sign_flip_p

class Tests(unittest.TestCase):
    def test_chart_is_accessible_and_labels_dependence(self):
        curve=[{"event_time_trading_day":i,"mean_direction_adjusted_cumulative_abnormal_log_return":i/100,"events":3} for i in range(-14,15)]
        svg=chart(curve,{"events_estimated":3,"assets":["a","b"]})
        self.assertIn('role="img"',svg); self.assertIn("positive values match",svg)

    def test_asset_sign_flip_uses_assets_not_events(self):
        p,assignments=exact_asset_sign_flip_p([.1,.2])
        self.assertEqual(assignments,4)
        self.assertEqual(p,.5)

if __name__=="__main__": unittest.main()
