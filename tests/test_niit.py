import unittest
from dataclasses import replace

from roth_conversions.config import load_inputs
from roth_conversions.models import NIITInputs
from roth_conversions.projection import project_with_tax_tracking
from roth_conversions.models import Strategy


class TestNIIT(unittest.TestCase):
    def test_niit_disabled_defaults_to_zero(self):
        inputs = load_inputs("configs/retirement_config.template.toml")
        inputs = replace(inputs, niit=NIITInputs(enabled=False))
        res = project_with_tax_tracking(inputs=inputs, strategy=Strategy("A", 0.0, 0), horizon_years=5)
        self.assertEqual(res.total_niit_tax, 0.0)
        self.assertTrue(all(y.niit_tax == 0.0 for y in res.yearly))

    def test_niit_enabled_is_non_negative(self):
        inputs = load_inputs("configs/retirement_config.template.toml")
        inputs = replace(inputs, niit=NIITInputs(enabled=True))
        res = project_with_tax_tracking(inputs=inputs, strategy=Strategy("A", 0.0, 0), horizon_years=5)
        self.assertGreaterEqual(res.total_niit_tax, 0.0)
        self.assertTrue(all(y.niit_tax >= 0.0 for y in res.yearly))

    def test_niit_realization_fraction_zero_disables_niit_effectively(self):
        inputs = load_inputs("configs/retirement_config.template.toml")
        inputs = replace(inputs, niit=NIITInputs(enabled=True, realization_fraction=0.0))
        res = project_with_tax_tracking(inputs=inputs, strategy=Strategy("A", 0.0, 0), horizon_years=5)
        self.assertEqual(res.total_niit_tax, 0.0)
        self.assertTrue(all(y.investment_income == 0.0 for y in res.yearly))

    def test_niit_increases_with_higher_realization_fraction(self):
        inputs = load_inputs("configs/retirement_config.template.toml")
        low = replace(inputs, niit=NIITInputs(enabled=True, realization_fraction=0.1, nii_fraction_of_return=0.7))
        high = replace(inputs, niit=NIITInputs(enabled=True, realization_fraction=1.0, nii_fraction_of_return=0.7))
        r_low = project_with_tax_tracking(inputs=low, strategy=Strategy("A", 0.0, 0), horizon_years=5)
        r_high = project_with_tax_tracking(inputs=high, strategy=Strategy("A", 0.0, 0), horizon_years=5)
        self.assertGreaterEqual(float(r_high.total_niit_tax), float(r_low.total_niit_tax))


if __name__ == "__main__":
    unittest.main()
