import unittest
from datetime import date, timedelta

from src.pipeline.crypto_mechanism_event_study import build


def spec():
    return {"schema_version":1,"document_version":"test","status":"frozen_before_event_estimation","freeze_date":"2026-09-07",
            "experiment_id":"P1_H5","panel":"x","ledger":"y","selection_rule":"All ledger events inside the panel.",
            "pre_window_days":5,"post_window_days":5,"minimum_days_per_window":3,"date_placebo_step_days":3,
            "outcomes":["log_market_cap_usd"],
            "events":[{"event_id":"t","asset_id":"treated","codes":["VA_BURN"],"effective_from":"2026-02-01",
                       "transition":"activation","expected_sign":"positive","announcement_caveat":"none"}],
            "interpretation":"Exploratory only."}


def ledger(extra=None):
    events=[{"asset_id":"treated","code":"VA_BURN","effective_from":"2026-02-01","value":1}]
    return {"events":events+(extra or [])}


def panel(effect=0.5, start="2026-01-01", days=62):
    rows=[]; first=date.fromisoformat(start); event=date(2026,2,1)
    for asset in ["treated","c1","c2","c3"]:
        for i in range(days):
            day=first+timedelta(days=i)
            level=10.0+(effect if asset=="treated" and day>event else 0.0)
            rows.append({"asset_id":asset,"date":day.isoformat(),"log_market_cap_usd":str(level)})
    return rows


class CryptoMechanismEventStudyTests(unittest.TestCase):
    def test_recovers_known_step_effect(self):
        results,summary=build(spec(),ledger(),panel())
        self.assertEqual(len(results),1)
        self.assertAlmostEqual(results[0]["difference_in_differences"],0.5)
        self.assertEqual(results[0]["controls_used"],3)
        self.assertEqual(summary["events_with_expected_sign"],1)
        self.assertLessEqual(results[0]["asset_placebo_p_two_sided"],0.25)

    def test_contaminated_control_is_excluded(self):
        extra=[{"asset_id":"c1","code":"VA_PROTOCOL","effective_from":"2026-02-03","value":1}]
        results,_=build(spec(),ledger(extra),panel())
        self.assertEqual(results[0]["controls"],"c2|c3")

    def test_window_outside_panel_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"outside the frozen panel"):
            build(spec(),ledger(),panel(start="2026-01-30",days=10))

    def test_event_must_match_ledger(self):
        with self.assertRaisesRegex(ValueError,"does not match"):
            build(spec(),{"events":[]},panel())


if __name__=="__main__": unittest.main()
