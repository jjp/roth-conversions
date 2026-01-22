import unittest
from dataclasses import replace

from roth_conversions.config import load_inputs
from roth_conversions.models import CharitableGivingInputs, JointAccounts, PlanInputs, SpouseInputs, Strategy
from roth_conversions.projection import project_with_tax_tracking


class TestQCD(unittest.TestCase):
    def test_qcd_reduces_taxable_income_and_tax(self):
        base = load_inputs("configs/retirement_config.template.toml")

        # Build a scenario where charitable giving must come from the IRA.
        no_qcd = replace(
            base,
            spouse1=replace(base.spouse1, age=71, traditional_ira=300_000.0, sep_ira=0.0, roth_ira=0.0, ss_annual=0.0),
            spouse2=replace(base.spouse2, age=71, traditional_ira=0.0, sep_ira=0.0, roth_ira=0.0, ss_annual=0.0),
            joint=JointAccounts(taxable_accounts=0.0),
            plan=PlanInputs(monthly_income_need=0.0, minimum_cash_reserve=0.0),
            charity=CharitableGivingInputs(enabled=True, annual_amount=80_000.0, use_qcd=False),
        )
        with_qcd = replace(no_qcd, charity=replace(no_qcd.charity, use_qcd=True))

        strat = Strategy("NoConversion", annual_conversion=0.0, conversion_years=0, allow_32_bracket=False)
        result_no_qcd = project_with_tax_tracking(inputs=no_qcd, strategy=strat, horizon_years=1)
        result_qcd = project_with_tax_tracking(inputs=with_qcd, strategy=strat, horizon_years=1)

        y_no_qcd = result_no_qcd.yearly[0]
        y_qcd = result_qcd.yearly[0]

        self.assertEqual(float(y_qcd.qcd), 80_000.0)
        self.assertGreater(float(y_no_qcd.income_tax), 0.0)
        self.assertEqual(float(y_qcd.income_tax), 0.0)


if __name__ == "__main__":
    unittest.main()
