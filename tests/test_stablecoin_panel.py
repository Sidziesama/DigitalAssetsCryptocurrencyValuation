import unittest

from src.pipeline.stablecoin_panel import build_panel, detect_episodes


class StablecoinPanelTests(unittest.TestCase):
    def test_panel_excludes_gold_target_and_calculates_bands(self):
        assets = [{"asset_id": "stable_x", "universe": "stablecoin", "tier": "market_core"}, {"asset_id": "stable_paxg", "universe": "stablecoin", "tier": "structural_coverage"}]
        prices = [{"asset_id": "stable_x", "date": "2026-01-01", "price_usd": "0.994", "provider": "p"}, {"asset_id": "stable_paxg", "date": "2026-01-01", "price_usd": "2000"}]
        rows = build_panel(assets, prices, [], [])
        self.assertEqual(len(rows), 1); self.assertEqual(rows[0]["breach_50bps"], 1); self.assertEqual(rows[0]["breach_100bps"], 0)

    def test_episode_recovery_and_metrics(self):
        rows = [
            {"asset_id": "x", "date": "2026-01-01", "signed_deviation_bps": -60},
            {"asset_id": "x", "date": "2026-01-02", "signed_deviation_bps": -40},
            {"asset_id": "x", "date": "2026-01-03", "signed_deviation_bps": -20},
        ]
        episode = detect_episodes(rows)[0]
        self.assertEqual(episode["recovery_date"], "2026-01-03"); self.assertEqual(episode["elapsed_days_to_recovery_or_censor"], 2)
        self.assertEqual(episode["observed_episode_days"], 2); self.assertEqual(episode["area_under_deviation_bps_days"], 100)

    def test_gap_censors_and_does_not_bridge(self):
        rows = [{"asset_id": "x", "date": "2026-01-01", "signed_deviation_bps": 60}, {"asset_id": "x", "date": "2026-01-03", "signed_deviation_bps": 60}]
        episodes = detect_episodes(rows)
        self.assertEqual(len(episodes), 2); self.assertEqual(episodes[0]["censor_reason"], "missing_calendar_gap")
        self.assertEqual(episodes[1]["censor_reason"], "sample_end")

    def test_recovery_band_must_be_narrower(self):
        with self.assertRaises(ValueError): detect_episodes([], 50, 50)

    def test_design_scores_are_not_backfilled_before_evidence_date(self):
        assets = [{"asset_id": "stable_x", "universe": "stablecoin", "tier": "market_core"}]
        prices = [{"asset_id": "stable_x", "date": "2025-01-01", "price_usd": "1"}, {"asset_id": "stable_x", "date": "2026-08-22", "price_usd": "1"}]
        scores = [{"asset_id": "stable_x", "evidence_date": "2026-08-22", "reserve_quality_score": "90", "methodology_version": "v1"}]
        rows = build_panel(assets, prices, [], scores)
        self.assertIsNone(rows[0]["reserve_quality_score"]); self.assertEqual(rows[1]["reserve_quality_score"], 90)


if __name__ == "__main__": unittest.main()
