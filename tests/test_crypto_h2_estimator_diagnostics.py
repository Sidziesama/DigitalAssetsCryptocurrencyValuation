import unittest

from src.pipeline.crypto_h2_estimator_diagnostics import POOLED_COLUMNS, matrix_rank, two_way_demean


class CryptoH2EstimatorDiagnosticsTests(unittest.TestCase):
    def test_pooled_model_includes_time_varying_capture_main_effect(self):
        self.assertIn("h2_active_capture", POOLED_COLUMNS)

    def test_matrix_rank_detects_collinearity(self):
        self.assertEqual(matrix_rank([[1,2],[2,4],[3,6]]),1)
        self.assertEqual(matrix_rank([[1,0],[0,1]]),2)

    def test_two_way_demean_removes_asset_and_date_means(self):
        rows=[
            {"asset_id":"a","date":"1","x":1.0},{"asset_id":"a","date":"2","x":3.0},
            {"asset_id":"b","date":"1","x":2.0},{"asset_id":"b","date":"2","x":6.0},
        ]
        transformed=two_way_demean(rows,("x",))
        for asset in {"a","b"}:
            values=[transformed[index][0] for index,row in enumerate(rows) if row["asset_id"]==asset]
            self.assertAlmostEqual(sum(values),0.0)
        for day in {"1","2"}:
            values=[transformed[index][0] for index,row in enumerate(rows) if row["date"]==day]
            self.assertAlmostEqual(sum(values),0.0)


if __name__=="__main__": unittest.main()
