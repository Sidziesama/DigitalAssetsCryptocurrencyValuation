import unittest
from datetime import date

from src.pipeline.crypto_h2_nonoverlap_sensitivity import assert_nonoverlap, partition_offsets


class CryptoH2NonoverlapSensitivityTests(unittest.TestCase):
    def test_offsets_partition_rows_and_space_dates(self):
        rows = [
            {"asset_id": "a", "date": date.fromordinal(date(2026, 1, 1).toordinal() + day).isoformat()}
            for day in range(21)
        ]
        partitions = partition_offsets(rows)
        self.assertEqual(sum(len(values) for values in partitions.values()), len(rows))
        self.assertEqual(
            {row["date"] for values in partitions.values() for row in values},
            {row["date"] for row in rows},
        )
        for values in partitions.values():
            assert_nonoverlap(values)

    def test_overlap_guard_rejects_adjacent_dates(self):
        with self.assertRaisesRegex(ValueError, "overlap"):
            assert_nonoverlap(
                [
                    {"date": "2026-01-01"},
                    {"date": "2026-01-07"},
                ]
            )


if __name__ == "__main__":
    unittest.main()
