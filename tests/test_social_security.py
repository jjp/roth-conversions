import unittest

from roth_conversions.social_security import taxable_social_security


class TestSocialSecurityTax(unittest.TestCase):
    def test_zero_other_income_no_taxable_ss(self):
        taxable = taxable_social_security(total_benefits=20_000, other_income=0, filing_status="MFJ")
        self.assertEqual(taxable, 0.0)

    def test_high_income_caps_at_85pct(self):
        taxable = taxable_social_security(total_benefits=40_000, other_income=200_000, filing_status="Single")
        self.assertAlmostEqual(taxable, 34_000.0, places=6)

    def test_mid_income_is_between_0_and_85pct(self):
        taxable = taxable_social_security(total_benefits=24_000, other_income=20_000, filing_status="Single")
        self.assertGreater(taxable, 0.0)
        self.assertLess(taxable, 0.85 * 24_000)


if __name__ == "__main__":
    unittest.main()
