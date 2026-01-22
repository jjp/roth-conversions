import unittest
from dataclasses import replace

from roth_conversions.config import load_inputs
from roth_conversions.models import Strategy
from roth_conversions.projection import project_with_tax_tracking


class TestRothFiveYearRule(unittest.TestCase):
    def test_roth_penalty_triggers_for_young_conversion_withdrawal(self):
        base = load_inputs("configs/retirement_config.template.toml")

        # Make the household "young" so the 10% penalty can apply.
        inputs = replace(
            base,
            spouse1=replace(base.spouse1, age=45, roth_ira=0.0),
            spouse2=replace(base.spouse2, age=45, roth_ira=0.0),
            # Need some taxable funds so the conversion-tax affordability constraint allows conversions.
            joint=replace(base.joint, taxable_accounts=300_000.0),
            plan=replace(base.plan, monthly_income_need=6_000.0, minimum_cash_reserve=0.0),
            roth_rules=replace(base.roth_rules, enabled=True, policy="penalty"),
        )

        # Convert in year 1, then withdraw from Roth in year 2.
        strat = Strategy("One-year convert", annual_conversion=100_000.0, conversion_years=1, allow_32_bracket=False)
        result = project_with_tax_tracking(inputs=inputs, strategy=strat, horizon_years=3)

        self.assertGreater(result.total_roth_penalty_tax, 0.0)
        self.assertTrue(any(y.roth_penalty_tax > 0.0 for y in result.yearly))


if __name__ == "__main__":
    unittest.main()
