import unittest
from dataclasses import replace

from roth_conversions.config import load_inputs
from roth_conversions.models import StateTaxInputs, Strategy
from roth_conversions.projection import project_with_tax_tracking


class TestStateTaxAndPartB(unittest.TestCase):
    def test_state_tax_enabled_adds_tax(self):
        inputs = load_inputs("configs/retirement_config.template.toml")
        inputs2 = replace(inputs, state_tax=StateTaxInputs(enabled=True, rate=0.05, base="agi"))

        res = project_with_tax_tracking(
            inputs=inputs2,
            strategy=Strategy("NoConv", annual_conversion=0.0, conversion_years=0, allow_32_bracket=False),
            horizon_years=1,
        )

        self.assertGreater(res.total_state_tax, 0.0)
        self.assertGreater(res.yearly[0].state_tax, 0.0)

    def test_part_b_base_premium_enabled_adds_cost(self):
        inputs = load_inputs("configs/retirement_config.template.toml")
        inputs2 = replace(
            inputs,
            medicare=replace(inputs.medicare, part_b_base_premium_enabled=True, covered_people=2),
        )

        res = project_with_tax_tracking(
            inputs=inputs2,
            strategy=Strategy("NoConv", annual_conversion=0.0, conversion_years=0, allow_32_bracket=False),
            horizon_years=1,
        )

        # 2025 base premium is pinned at $185/month.
        self.assertAlmostEqual(res.total_medicare_part_b_base_premium_cost, 185.0 * 12.0 * 2.0, places=6)
        self.assertAlmostEqual(res.yearly[0].medicare_part_b_base_premium_cost, 185.0 * 12.0 * 2.0, places=6)


if __name__ == "__main__":
    unittest.main()
