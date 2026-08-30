import unittest

from src.pipeline.crypto_h2_small_cluster_inference import (
    cluster_standard_errors,
    fit,
    inverse,
    multiply,
)


class CryptoH2SmallClusterInferenceTests(unittest.TestCase):
    def test_inverse_multiplies_to_identity(self):
        matrix = [[4.0, 1.0], [1.0, 3.0]]
        product = multiply(matrix, inverse(matrix))
        self.assertAlmostEqual(product[0][0], 1.0)
        self.assertAlmostEqual(product[0][1], 0.0)
        self.assertAlmostEqual(product[1][0], 0.0)
        self.assertAlmostEqual(product[1][1], 1.0)

    def test_cluster_standard_errors_are_finite(self):
        x = [[1.0], [2.0], [1.5], [3.0]]
        y = [2.0, 4.2, 2.7, 6.4]
        _, _, residuals, xtx_inverse = fit(x, y)
        standard_errors = cluster_standard_errors(x, residuals, ["a", "a", "b", "b"], xtx_inverse)
        self.assertEqual(len(standard_errors), 1)
        self.assertGreater(standard_errors[0], 0.0)


if __name__ == "__main__":
    unittest.main()
