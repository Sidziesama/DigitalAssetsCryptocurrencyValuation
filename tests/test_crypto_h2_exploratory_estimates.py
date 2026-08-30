import unittest

from src.pipeline.crypto_h2_exploratory_estimates import estimate, solve


class CryptoH2ExploratoryEstimatesTests(unittest.TestCase):
    def test_solve_recovers_linear_system(self):
        result = solve([[2.0, 0.0], [0.0, 4.0]], [6.0, 8.0])
        self.assertEqual(result, [3.0, 2.0])

    def test_two_way_fe_estimate_recovers_coefficient(self):
        rows = []
        x_values = {
            ("a", "1"): 1.0,
            ("a", "2"): 4.0,
            ("b", "1"): 3.0,
            ("b", "2"): 2.0,
        }
        asset_effect = {"a": 5.0, "b": -2.0}
        date_effect = {"1": 7.0, "2": -1.0}
        for (asset_id, date), x_value in x_values.items():
            rows.append(
                {
                    "asset_id": asset_id,
                    "date": date,
                    "x": x_value,
                    "y": 2.5 * x_value + asset_effect[asset_id] + date_effect[date],
                }
            )
        result = estimate("synthetic", rows, "y", ("x",))
        self.assertAlmostEqual(result["coefficients"]["x"], 2.5)
        self.assertAlmostEqual(result["within_r_squared"], 1.0)
        self.assertIsNone(result["p_values"])


if __name__ == "__main__":
    unittest.main()
