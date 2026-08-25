import unittest

from src.pipeline.stablecoin_atlas import asset_statistics, quantile, review_queue


class StablecoinAtlasTests(unittest.TestCase):
    def test_interpolated_quantile(self):
        self.assertEqual(quantile([0, 10], .25), 2.5)
        with self.assertRaises(ValueError): quantile([1], 2)

    def test_statistics_keep_failure_control_visible(self):
        panel = [{"asset_id": "x", "date": "2026-01-01", "sample_tier": "failure_control", "failure_control": "1", "absolute_peg_error_bps": "100", "signed_deviation_bps": "-100", **{f"breach_{band}bps": "1" for band in (10, 25, 50, 100, 500)}}]
        episodes = [{"asset_id": "x", "elapsed_days_to_recovery_or_censor": "2", "recovered": "0", "right_censored": "1", "area_under_deviation_bps_days": "200"}]
        row = asset_statistics(panel, episodes)[0]
        self.assertEqual(row["failure_control"], 1); self.assertEqual(row["episode_count_50bps"], 1)

    def test_review_queue_distinguishes_source_check(self):
        episodes = [{"episode_id": "e", "asset_id": "x", "onset_date": "2026-01-01", "last_episode_date": "2026-01-01", "maximum_absolute_deviation_bps": "3000", "data_review_flag": "1", "failure_control": "0"}]
        self.assertEqual(review_queue(episodes)[0]["review_class"], "source_crosscheck_required")


if __name__ == "__main__": unittest.main()
