import unittest
from dataclasses import replace

from roth_conversions.config import load_inputs
from roth_conversions.models import CharitableGivingInputs, JointAccounts, PlanInputs
from roth_conversions.analysis.home_purchase import project_with_home_purchase


class TestHomePurchaseQCD(unittest.TestCase):
    def test_home_purchase_scenario_qcd_reduces_income_tax(self):
        base = load_inputs("configs/retirement_config.template.toml")

        # No SS, no spending, no taxable/roth. Charitable giving must come from IRA.
        base_case = replace(
            base,
            spouse1=replace(base.spouse1, age=71, traditional_ira=300_000.0, sep_ira=0.0, roth_ira=0.0, ss_annual=0.0),
            spouse2=replace(base.spouse2, age=71, traditional_ira=0.0, sep_ira=0.0, roth_ira=0.0, ss_annual=0.0),
            joint=JointAccounts(taxable_accounts=0.0),
            plan=PlanInputs(monthly_income_need=0.0, minimum_cash_reserve=0.0),
        )

        no_qcd_inputs = replace(
            base_case,
            charity=CharitableGivingInputs(enabled=True, annual_amount=80_000.0, use_qcd=False, qcd_eligible_age=71),
        )
        qcd_inputs = replace(
            base_case,
            charity=CharitableGivingInputs(enabled=True, annual_amount=80_000.0, use_qcd=True, qcd_eligible_age=71),
        )

        no_qcd = project_with_home_purchase(
            inputs=no_qcd_inputs,
            purchase_year=int(no_qcd_inputs.household.start_year),
            down_payment=0.0,
            conversion_years=0,
            max_annual_conv=0.0,
            horizon_years=1,
        )
        with_qcd = project_with_home_purchase(
            inputs=qcd_inputs,
            purchase_year=int(qcd_inputs.household.start_year),
            down_payment=0.0,
            conversion_years=0,
            max_annual_conv=0.0,
            horizon_years=1,
        )

        y_no = no_qcd.yearly_data[0]
        y_qcd = with_qcd.yearly_data[0]

        self.assertEqual(float(y_qcd.get("qcd", 0.0)), 80_000.0)
        self.assertGreater(float(y_no.get("income_tax", 0.0)), 0.0)
        self.assertEqual(float(y_qcd.get("income_tax", 0.0)), 0.0)


if __name__ == "__main__":
    unittest.main()
