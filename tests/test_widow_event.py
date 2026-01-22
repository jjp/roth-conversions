import unittest
from dataclasses import replace

from roth_conversions.config import load_inputs
from roth_conversions.models import Strategy, WidowEventInputs
from roth_conversions.projection import project_with_tax_tracking


class TestWidowEvent(unittest.TestCase):
    def test_widow_event_switches_to_survivor_ss(self):
        base = load_inputs("configs/retirement_config.template.toml")
        # Start in 2025; widow event in 2026 (year index 1).
        inputs = replace(
            base,
            widow_event=WidowEventInputs(
                enabled=True,
                widow_year=base.household.start_year + 1,
                survivor="spouse1",
                income_need_multiplier=1.0,
            ),
        )

        strat = Strategy("NoConversion", annual_conversion=0, conversion_years=0, allow_32_bracket=False)
        result = project_with_tax_tracking(inputs=inputs, strategy=strat, horizon_years=2)

        year1 = result.yearly[0]  # 2025
        year2 = result.yearly[1]  # 2026

        # In the shipped template inputs, both spouses are already receiving SS in year1.
        self.assertEqual(year1.ss_income, 48_000 + 28_000)

        # After widow event, SS becomes the survivor benefit (max of the two).
        self.assertEqual(year2.ss_income, 48_000)


if __name__ == "__main__":
    unittest.main()
