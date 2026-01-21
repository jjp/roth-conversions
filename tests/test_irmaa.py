import unittest
from dataclasses import replace

from roth_conversions.config import load_inputs
from roth_conversions.models import MedicareInputs, Strategy
from roth_conversions.projection import project_with_tax_tracking


class TestIrmaa(unittest.TestCase):
    def test_irmaa_disabled_defaults_to_zero(self):
        inputs = load_inputs("configs/retirement_config.template.toml")
        inputs = replace(inputs, medicare=MedicareInputs(irmaa_enabled=False))
        strat = Strategy("OneYear", annual_conversion=0, conversion_years=0, allow_32_bracket=False)
        result = project_with_tax_tracking(inputs=inputs, strategy=strat, horizon_years=1)
        self.assertEqual(result.yearly[0].irmaa_cost, 0.0)
        self.assertEqual(result.total_irmaa_cost, 0.0)

    def test_irmaa_uses_lookback_years(self):
        inputs = load_inputs("configs/retirement_config.template.toml")
        # Force IRMAA on, and force year-1 MAGI high via a big one-time conversion.
        inputs = replace(inputs, medicare=MedicareInputs(irmaa_enabled=True))
        strat = Strategy("FrontLoad", annual_conversion=400_000, conversion_years=1, allow_32_bracket=True)

        # Need at least 3 years so year 3 uses year 1 MAGI (2-year lookback).
        result = project_with_tax_tracking(inputs=inputs, strategy=strat, horizon_years=3)

        year1 = result.yearly[0]
        year2 = result.yearly[1]
        year3 = result.yearly[2]

        # Year 1 may already have IRMAA (fallback uses current MAGI when lookback missing).
        self.assertGreaterEqual(year1.irmaa_cost, 0.0)

        # Year 3 should reflect the (high) year-1 MAGI due to lookback.
        self.assertGreater(year3.irmaa_cost, 0.0)

        # With a one-year conversion, current-year MAGI should drop after year 1;
        # lookback keeps IRMAA elevated in year 3.
        self.assertGreaterEqual(year3.irmaa_cost, year2.irmaa_cost)


if __name__ == "__main__":
    unittest.main()
