import unittest

from roth_conversions.tax import calculate_tax_mfj_2024, marginal_rate_mfj_2024


class TestTax(unittest.TestCase):
    def test_zero_income_tax_is_zero(self):
        self.assertEqual(calculate_tax_mfj_2024(0), 0.0)
        self.assertEqual(calculate_tax_mfj_2024(-100), 0.0)

    def test_first_bracket_edge(self):
        # 10% up to 23,200
        self.assertAlmostEqual(calculate_tax_mfj_2024(23_200), 2_320.0, places=6)

    def test_marginal_rate(self):
        self.assertAlmostEqual(marginal_rate_mfj_2024(1), 0.10)
        self.assertAlmostEqual(marginal_rate_mfj_2024(23_200), 0.10)
        self.assertAlmostEqual(marginal_rate_mfj_2024(23_201), 0.12)


if __name__ == "__main__":
    unittest.main()
