import unittest

from roth_conversions.tax import calculate_tax_federal_ltcg_qd_simple


class TestPreferentialTax(unittest.TestCase):
    def test_mfj_2024_ltcg_at_zero_threshold_is_zero_tax(self):
        tax = calculate_tax_federal_ltcg_qd_simple(
            ordinary_income=0.0,
            qualified_dividends=0.0,
            long_term_capital_gains=94_050.0,
            deduction=0.0,
            tax_year=2024,
            filing_status="MFJ",
        )
        self.assertAlmostEqual(tax, 0.0, places=6)

    def test_mfj_2024_one_dollar_over_zero_threshold_taxed_at_15pct(self):
        tax = calculate_tax_federal_ltcg_qd_simple(
            ordinary_income=0.0,
            qualified_dividends=0.0,
            long_term_capital_gains=94_051.0,
            deduction=0.0,
            tax_year=2024,
            filing_status="MFJ",
        )
        self.assertAlmostEqual(tax, 0.15, places=6)

    def test_mfj_2024_stacking_with_ordinary_income_reduces_0pct_room(self):
        # Ordinary taxable income fills the bottom first.
        # Ordinary=50k and LTCG=50k with no deduction:
        # - 0% LTCG room = 94,050 - 50,000 = 44,050
        # - remaining LTCG taxed at 15%: 50,000 - 44,050 = 5,950 => 892.50
        # - ordinary tax at 50k MFJ 2024: 2,320 + 0.12*(50,000-23,200)=5,536
        # - total = 5,536 + 892.50 = 6,428.50
        tax = calculate_tax_federal_ltcg_qd_simple(
            ordinary_income=50_000.0,
            qualified_dividends=0.0,
            long_term_capital_gains=50_000.0,
            deduction=0.0,
            tax_year=2024,
            filing_status="MFJ",
        )
        self.assertAlmostEqual(tax, 6_428.50, places=2)


if __name__ == "__main__":
    unittest.main()
