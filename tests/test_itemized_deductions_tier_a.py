import unittest

from roth_conversions.models import (
    Household,
    HouseholdInputs,
    ItemizedDeductionsInputs,
    JointAccounts,
    PlanInputs,
    PreferentialIncomeInputs,
    ReturnAssumptions,
    SpouseInputs,
    Strategy,
)
from roth_conversions.projection import project_with_tax_tracking


class TestItemizedDeductionsTierA(unittest.TestCase):
    def test_large_itemized_deduction_can_zero_out_income_tax(self):
        inputs = HouseholdInputs(
            household=Household(tax_filing_status="MFJ", start_year=2025, discount_rate=0.0),
            spouse1=SpouseInputs(
                name="A",
                age=70,
                traditional_ira=500_000.0,
                sep_ira=0.0,
                roth_ira=0.0,
                ss_start_age=90,
                ss_annual=0.0,
            ),
            spouse2=SpouseInputs(
                name="B",
                age=70,
                traditional_ira=500_000.0,
                sep_ira=0.0,
                roth_ira=0.0,
                ss_start_age=90,
                ss_annual=0.0,
            ),
            joint=JointAccounts(taxable_accounts=100_000.0),
            plan=PlanInputs(monthly_income_need=5_000.0, minimum_cash_reserve=0.0),
            assumptions=ReturnAssumptions(inflation_rate=0.0, taxable_return=0.0, ira_return=0.0, roth_return=0.0),
            preferential_income=PreferentialIncomeInputs(qualified_dividends_annual=0.0, long_term_capital_gains_annual=0.0),
            itemized_deductions=ItemizedDeductionsInputs(enabled=True, itemized_deductions_annual=1_000_000_000.0),
        )

        strat = Strategy("No conversions", annual_conversion=0.0, conversion_years=0)
        result = project_with_tax_tracking(inputs=inputs, strategy=strat, horizon_years=1)

        self.assertEqual(len(result.yearly), 1)
        self.assertAlmostEqual(result.yearly[0].income_tax, 0.0, places=6)


if __name__ == "__main__":
    unittest.main()
