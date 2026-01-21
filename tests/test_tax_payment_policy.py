import unittest
from dataclasses import replace

from roth_conversions.config import load_inputs
from roth_conversions.models import Strategy, TaxPaymentPolicy
from roth_conversions.projection import project_with_tax_tracking


class TestTaxPaymentPolicy(unittest.TestCase):
    def test_conversion_tax_payment_source_affects_balances(self):
        inputs = load_inputs("configs/retirement_config.template.toml")
        strat = Strategy("OneYear", annual_conversion=50_000, conversion_years=1, allow_32_bracket=False)

        inputs_taxable = replace(
            inputs,
            tax_payment_policy=TaxPaymentPolicy(
                income_tax_payment_source="taxable",
                conversion_tax_payment_source="taxable",
            ),
        )
        inputs_ira = replace(
            inputs,
            tax_payment_policy=TaxPaymentPolicy(
                income_tax_payment_source="taxable",
                conversion_tax_payment_source="ira",
            ),
        )

        r_taxable = project_with_tax_tracking(inputs=inputs_taxable, strategy=strat, horizon_years=1)
        r_ira = project_with_tax_tracking(inputs=inputs_ira, strategy=strat, horizon_years=1)

        self.assertGreater(r_ira.yearly[0].taxable_end, r_taxable.yearly[0].taxable_end)
        self.assertLess(r_ira.yearly[0].ira_end, r_taxable.yearly[0].ira_end)

    def test_income_tax_payment_source_affects_balances(self):
        inputs = load_inputs("configs/retirement_config.template.toml")
        strat = Strategy("NoConversion", annual_conversion=0, conversion_years=0, allow_32_bracket=False)

        inputs_taxable = replace(
            inputs,
            tax_payment_policy=TaxPaymentPolicy(
                income_tax_payment_source="taxable",
                conversion_tax_payment_source="taxable",
            ),
        )
        inputs_ira = replace(
            inputs,
            tax_payment_policy=TaxPaymentPolicy(
                income_tax_payment_source="ira",
                conversion_tax_payment_source="taxable",
            ),
        )

        r_taxable = project_with_tax_tracking(inputs=inputs_taxable, strategy=strat, horizon_years=1)
        r_ira = project_with_tax_tracking(inputs=inputs_ira, strategy=strat, horizon_years=1)

        self.assertGreater(r_ira.yearly[0].taxable_end, r_taxable.yearly[0].taxable_end)
        self.assertLess(r_ira.yearly[0].ira_end, r_taxable.yearly[0].ira_end)


if __name__ == "__main__":
    unittest.main()
