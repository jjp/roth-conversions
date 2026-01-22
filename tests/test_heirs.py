import unittest
from dataclasses import replace

from roth_conversions.config import load_inputs
from roth_conversions.models import HeirsInputs, JointAccounts, PlanInputs, Strategy
from roth_conversions.projection import project_with_tax_tracking


class TestHeirs(unittest.TestCase):
    def test_ten_year_window_allows_more_tax_deferred_growth_than_five_year(self):
        base = load_inputs("configs/retirement_config.template.toml")

        # No spending, no SS, so the IRA just compounds for 1 year.
        base_case = replace(
            base,
            spouse1=replace(base.spouse1, age=60, ss_annual=0.0),
            spouse2=replace(base.spouse2, age=60, traditional_ira=0.0, ss_annual=0.0, roth_ira=0.0),
            joint=JointAccounts(taxable_accounts=0.0),
            plan=PlanInputs(monthly_income_need=0.0, minimum_cash_reserve=0.0),
        )

        five_year = replace(base_case, heirs=HeirsInputs(enabled=True, distribution_years=5, heir_tax_rate=0.30))
        ten_year = replace(base_case, heirs=HeirsInputs(enabled=True, distribution_years=10, heir_tax_rate=0.30))

        strat = Strategy("NoConversion", annual_conversion=0.0, conversion_years=0, allow_32_bracket=False)
        r5 = project_with_tax_tracking(inputs=five_year, strategy=strat, horizon_years=1)
        r10 = project_with_tax_tracking(inputs=ten_year, strategy=strat, horizon_years=1)

        self.assertGreater(float(r10.heirs_after_tax), float(r5.heirs_after_tax))


if __name__ == "__main__":
    unittest.main()
