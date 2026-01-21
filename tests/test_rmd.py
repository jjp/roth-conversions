import unittest

from roth_conversions.rmd import rmd_divisor, required_minimum_distribution


class TestRmd(unittest.TestCase):
    def test_no_rmd_before_73(self):
        self.assertIsNone(rmd_divisor(72))
        self.assertEqual(required_minimum_distribution(100_000, 72), 0.0)

    def test_rmd_at_73(self):
        self.assertAlmostEqual(rmd_divisor(73), 26.5)
        self.assertAlmostEqual(required_minimum_distribution(265_000, 73), 10_000.0, places=6)

    def test_rmd_default_for_95_plus(self):
        self.assertAlmostEqual(rmd_divisor(120), 8.9)


if __name__ == "__main__":
    unittest.main()
