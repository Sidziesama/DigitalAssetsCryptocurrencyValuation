import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from src.pipeline.historical import chunk_ranges, coverage_record, longest_missing_run, market_chart_url, merge_rows, normalize_daily
from src.pipeline.registry import load_env_file


class HistoricalTests(unittest.TestCase):
    def test_normalizes_last_value_per_utc_day(self):
        payload={"prices":[[0,1.0],[86399000,2.0],[86400000,3.0]],"market_caps":[[0,10.0]],"total_volumes":[[0,5.0]]}
        rows=normalize_daily(payload)
        self.assertEqual(rows[0]["date"],"1970-01-01")
        self.assertEqual(rows[0]["price_usd"],2.0)
        self.assertEqual(rows[1]["price_usd"],3.0)

    def test_coverage_detects_gap(self):
        rows=[{"date":"2026-01-01","price_usd":1},{"date":"2026-01-03","price_usd":1}]
        result=coverage_record("x",rows,date(2026,1,1),date(2026,1,3))
        self.assertAlmostEqual(result["coverage_ratio"],2/3)
        self.assertEqual(result["longest_missing_run_days"],1)
        self.assertEqual(result["status"],"review")

    def test_longest_missing_run_at_boundary(self):
        self.assertEqual(longest_missing_run({date(2026,1,2)},date(2026,1,1),date(2026,1,4)),2)

    def test_url_encodes_parameters(self):
        url=market_chart_url("https://example.test/api", "coin id", date(2026,1,1), date(2026,1,2))
        self.assertIn("coin%20id",url)
        self.assertIn("vs_currency=usd",url)

    def test_chunks_are_contiguous(self):
        chunks=chunk_ranges(date(2020,1,1),date(2020,1,5),2)
        self.assertEqual(chunks,[(date(2020,1,1),date(2020,1,2)),(date(2020,1,3),date(2020,1,4)),(date(2020,1,5),date(2020,1,5))])

    def test_incremental_merge_replaces_same_key(self):
        rows=merge_rows([{"asset_id":"a","date":"2026-01-01","price_usd":"1"}],[{"asset_id":"a","date":"2026-01-01","price_usd":2}],("asset_id","date"))
        self.assertEqual(rows[0]["price_usd"],2)

    def test_loads_local_env_without_overriding_shell(self):
        with TemporaryDirectory() as directory, patch.dict("os.environ", {"EXISTING_KEY": "shell"}, clear=True):
            path = Path(directory) / ".env"
            path.write_text("# local keys\nAPI_KEY='secret'\nEXISTING_KEY=file\n", encoding="utf-8")
            loaded = load_env_file(path)
            self.assertEqual(loaded["API_KEY"], "secret")
            self.assertEqual(__import__("os").environ["API_KEY"], "secret")
            self.assertEqual(__import__("os").environ["EXISTING_KEY"], "shell")


if __name__ == "__main__": unittest.main()
