import unittest
from src.pipeline.crypto_h3_supply_event_analysis import chart

class Tests(unittest.TestCase):
    def test_chart_is_accessible_and_labels_dependence(self):
        curve=[{"event_time_trading_day":i,"mean_cumulative_abnormal_log_return":i/100,"events":3} for i in range(-14,15)]
        svg=chart(curve,{"events_estimated":3})
        self.assertIn('role="img"',svg); self.assertIn("descriptive, not independent",svg)

if __name__=="__main__": unittest.main()
