from __future__ import annotations

from dataclasses import dataclass

from ..models import HouseholdInputs
from ..rmd import required_minimum_distribution


@dataclass(frozen=True)
class HomePurchaseScenario:
    purchase_year: int
    down_payment: float
    total_conversions: float
    total_rmds: float
    total_rmd_tax: float
    after_tax: float
    legacy: float
    yearly_data: tuple[dict, ...]


def project_with_home_purchase(
    *,
    inputs: HouseholdInputs,
    purchase_year: int,
    down_payment: float,
    conversion_years: int = 5,
    max_annual_conv: float = 150_000.0,
    horizon_years: int = 25,
) -> HomePurchaseScenario:
    """Refactor of notebook Chapter 8 (cell_22) with RMDs + home purchase drawdown."""

    base_year = int(inputs.household.start_year)
    purchase_year_offset = int(purchase_year) - base_year

    ira = float(inputs.total_pretax)
    roth = float(inputs.total_roth)
    taxable = float(inputs.joint.taxable_accounts)

    # Home purchase split logic from notebook
    split_taxable = min(down_payment // 2, taxable - float(inputs.plan.minimum_cash_reserve))
    split_ira_net = down_payment - split_taxable
    split_ira_gross = split_ira_net * 1.24

    total_conversions = 0.0
    total_rmds = 0.0
    total_rmd_tax = 0.0

    yearly_data: list[dict] = []

    for yr in range(horizon_years):
        spouse1_age = int(inputs.spouse1.age) + yr
        spouse2_age = int(inputs.spouse2.age) + yr
        calendar_year = base_year + yr

        year: dict[str, object] = {
            "year": yr + 1,
            "calendar_year": calendar_year,
            "spouse1_age": spouse1_age,
            "spouse2_age": spouse2_age,
        }
        year["ira_start"] = ira
        year["roth_start"] = roth
        year["taxable_start"] = taxable

        spouse1_rmd = required_minimum_distribution(ira * 0.33, spouse1_age)
        spouse2_rmd = required_minimum_distribution(ira * 0.67, spouse2_age)
        total_rmd_this_year = spouse1_rmd + spouse2_rmd
        ira -= total_rmd_this_year
        total_rmds += total_rmd_this_year

        rmd_tax = total_rmd_this_year * 0.24
        total_rmd_tax += rmd_tax

        year["rmd"] = total_rmd_this_year
        year["rmd_tax"] = rmd_tax

        home_this_year = yr == purchase_year_offset
        if home_this_year:
            taxable -= split_taxable
            ira -= split_ira_gross
            year["home_purchase"] = True
            year["home_from_taxable"] = split_taxable
            year["home_from_ira"] = split_ira_gross
        else:
            year["home_purchase"] = False

        # Conversions
        conversion = 0.0
        if yr < int(conversion_years):
            available_for_tax = taxable - float(inputs.plan.minimum_cash_reserve)
            if yr < purchase_year_offset:
                available_for_tax -= float(down_payment)

            if available_for_tax > 0:
                max_from_funds = available_for_tax / 0.24
                max_this_year = 75_000.0 if home_this_year else float(max_annual_conv)
                conversion = min(max_from_funds, max_this_year, ira)
                conversion = max(0.0, conversion)

        conv_tax = conversion * 0.24 if conversion > 0 else 0.0
        if conversion > 0:
            ira -= conversion
            roth += conversion
            taxable -= conv_tax
            total_conversions += conversion

        year["conversion"] = conversion
        year["conv_tax"] = conv_tax

        # Spending
        income_need = float(inputs.plan.annual_income_need) * (1.0 + float(inputs.assumptions.inflation_rate)) ** yr
        ss1 = float(inputs.spouse1.ss_annual) if yr >= inputs.years_to_spouse1_ss else 0.0
        ss2 = float(inputs.spouse2.ss_annual) if yr >= inputs.years_to_spouse2_ss else 0.0
        total_ss = ss1 + ss2

        from_rmd_for_spending = min(total_rmd_this_year * 0.76, max(0.0, income_need - total_ss))
        remaining_need = max(0.0, income_need - total_ss - from_rmd_for_spending)

        from_taxable = min(remaining_need * 0.3, taxable - float(inputs.plan.minimum_cash_reserve))
        from_roth = min(remaining_need * 0.2, roth)
        from_ira = remaining_need - from_taxable - from_roth

        taxable -= max(0.0, from_taxable)
        roth -= max(0.0, from_roth)
        ira -= max(0.0, from_ira * 1.24)

        # Growth
        ira *= (1.0 + float(inputs.assumptions.ira_return))
        roth *= (1.0 + float(inputs.assumptions.roth_return))
        taxable *= (1.0 + float(inputs.assumptions.taxable_return))

        year["ira_end"] = ira
        year["roth_end"] = roth
        year["taxable_end"] = taxable

        yearly_data.append(year)

    after_tax = ira * 0.75 + roth + taxable * 0.92
    legacy = ira * (1.0 - 0.28) + roth + taxable * 0.95

    return HomePurchaseScenario(
        purchase_year=purchase_year,
        down_payment=down_payment,
        total_conversions=total_conversions,
        total_rmds=total_rmds,
        total_rmd_tax=total_rmd_tax,
        after_tax=after_tax,
        legacy=legacy,
        yearly_data=tuple(yearly_data),
    )
