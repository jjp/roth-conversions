import unittest

from roth_conversions import irmaa_tables, tax_tables


class TestPinnedTaxTablesGolden(unittest.TestCase):
    def test_tax_year_resolution_caps_to_latest_pinned(self):
        # If future-year tables are not yet pinned, we use the latest pinned year <= requested.
        self.assertEqual(tax_tables.resolve_tax_year(2099), 2026)

    def test_tax_year_resolution_raises_before_first_pinned(self):
        with self.assertRaises(ValueError):
            tax_tables.resolve_tax_year(2023)

    def test_2026_standard_deduction(self):
        self.assertEqual(tax_tables.get_standard_deduction(tax_year=2026, filing_status="MFJ"), 32_200.0)
        self.assertEqual(tax_tables.get_standard_deduction(tax_year=2026, filing_status="Single"), 16_100.0)

    def test_2026_mfj_bracket_ceiling_24pct(self):
        self.assertEqual(tax_tables.get_bracket_ceiling(tax_year=2026, filing_status="MFJ", rate=0.24), 403_550.0)

    def test_2026_mfj_tax_known_points(self):
        brackets = tax_tables.get_ordinary_income_brackets(tax_year=2026, filing_status="MFJ")

        # Exactly at the 12% bracket ceiling.
        # 10% up to 24,800; 12% on (100,800-24,800)=76,000
        self.assertAlmostEqual(tax_tables.calculate_tax(100_800.0, brackets), 11_600.0, places=6)

        # Exactly at the 22% bracket ceiling.
        # Prior tax: 11,600; plus 22% on (211,400-100,800)=110,600
        self.assertAlmostEqual(tax_tables.calculate_tax(211_400.0, brackets), 35_932.0, places=6)


class TestPinnedIrmaaTablesGolden(unittest.TestCase):
    def test_premium_year_resolution_caps_to_latest_pinned(self):
        self.assertEqual(irmaa_tables.resolve_premium_year(2099), 2026)

    def test_premium_year_resolution_raises_before_first_pinned(self):
        with self.assertRaises(ValueError):
            irmaa_tables.resolve_premium_year(2024)

    def test_2026_mfj_tiers(self):
        # 2026 MFJ tier 1 max is 218,000 => 0 add-ons.
        b0, d0 = irmaa_tables.get_irmaa_addons_monthly(premium_year=2026, filing_status="MFJ", magi=218_000.0)
        self.assertEqual((b0, d0), (0.0, 0.0))

        # 2026 MFJ tier 2 applies above 218,000 up to 274,000.
        b1, d1 = irmaa_tables.get_irmaa_addons_monthly(premium_year=2026, filing_status="MFJ", magi=218_001.0)
        self.assertEqual((b1, d1), (81.2, 14.5))

        # Top tier returns the final add-ons.
        b2, d2 = irmaa_tables.get_irmaa_addons_monthly(premium_year=2026, filing_status="MFJ", magi=1_000_000_000.0)
        self.assertEqual((b2, d2), (487.0, 91.0))


if __name__ == "__main__":
    unittest.main()
