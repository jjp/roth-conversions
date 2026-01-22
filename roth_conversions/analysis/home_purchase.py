from __future__ import annotations

from dataclasses import dataclass

from ..models import HouseholdInputs
from ..roth_rules import RothLedger
from ..irmaa_tables import get_irmaa_addons_monthly
from ..medicare_part_b_tables import get_part_b_base_premium_monthly
from ..rmd import required_minimum_distribution
from ..social_security import taxable_social_security
from ..tax import calculate_tax_ordinary_income, marginal_rate_ordinary_income
from ..tax_tables import get_bracket_ceiling, get_standard_deduction
from ..withdrawal_policy import pay_tax
from ..niit import calculate_niit


@dataclass(frozen=True)
class HomePurchaseScenario:
    purchase_year: int
    down_payment: float
    total_conversions: float
    total_rmds: float
    total_rmd_tax: float
    total_irmaa_cost: float
    total_medicare_part_b_base_premium_cost: float
    total_state_tax: float
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

    roth_ledger = RothLedger(basis_remaining=float(roth), buckets=[])

    base_filing_status = str(inputs.household.tax_filing_status)
    tax_policy = inputs.tax_payment_policy
    widow_event = inputs.widow_event
    charity = inputs.charity

    total_conversions = 0.0
    total_rmds = 0.0
    total_rmd_tax = 0.0
    total_irmaa_cost = 0.0
    total_medicare_part_b_base_premium_cost = 0.0
    total_state_tax = 0.0

    magi_by_calendar_year: dict[int, float] = {}

    yearly_data: list[dict] = []

    for yr in range(horizon_years):
        spouse1_age = int(inputs.spouse1.age) + yr
        spouse2_age = int(inputs.spouse2.age) + yr
        calendar_year = base_year + yr

        inflation_multiplier = (1.0 + float(inputs.assumptions.inflation_rate)) ** yr

        widow_active = bool(widow_event.enabled) and widow_event.widow_year is not None and calendar_year >= int(widow_event.widow_year)
        filing_status = "Single" if widow_active else base_filing_status

        year: dict[str, object] = {
            "year": yr + 1,
            "calendar_year": calendar_year,
            "spouse1_age": spouse1_age,
            "spouse2_age": spouse2_age,
            "inflation_multiplier": inflation_multiplier,
        }
        year["ira_start"] = ira
        year["roth_start"] = roth
        year["taxable_start"] = taxable

        # Standard deduction (pinned), used by the tax engine.
        try:
            standard_deduction = get_standard_deduction(tax_year=calendar_year, filing_status=filing_status)
        except Exception:
            standard_deduction = 30_000.0

        # RMDs
        spouse1_rmd = required_minimum_distribution(ira * 0.33, spouse1_age)
        spouse2_rmd = required_minimum_distribution(ira * 0.67, spouse2_age)
        total_rmd_this_year = spouse1_rmd + spouse2_rmd
        total_rmds += total_rmd_this_year

        # Social security (widow modeling: survivor benefit)
        ss1 = float(inputs.spouse1.ss_annual) if yr >= inputs.years_to_spouse1_ss else 0.0
        ss2 = float(inputs.spouse2.ss_annual) if yr >= inputs.years_to_spouse2_ss else 0.0
        total_ss = max(ss1, ss2) if widow_active else (ss1 + ss2)
        year["ss_income"] = total_ss

        # Base spending need + one-time home purchase cash need.
        income_need_multiplier = float(widow_event.income_need_multiplier) if widow_active else 1.0
        income_need = (
            float(inputs.plan.annual_income_need)
            * inflation_multiplier
            * income_need_multiplier
        )
        year["income_need"] = income_need

        charity_need = 0.0
        qcd = 0.0
        if bool(charity.enabled) and float(charity.annual_amount) > 0:
            charity_need = float(charity.annual_amount) * inflation_multiplier
            if bool(charity.use_qcd):
                eligible = (spouse1_age >= int(charity.qcd_eligible_age)) or (spouse2_age >= int(charity.qcd_eligible_age))
                if eligible:
                    covered_people = 2 if filing_status == "MFJ" else 1
                    cap = float(charity.qcd_annual_cap_per_person) * float(covered_people)
                    qcd = min(charity_need, cap, max(0.0, ira))

        year["charity_need"] = charity_need
        year["qcd"] = qcd
        home_this_year = yr == purchase_year_offset
        home_cash_need = float(down_payment) if home_this_year else 0.0

        # From savings needed for annual spending (not including the home one-time need).
        # Include charitable giving as a planned cash need; QCD (if any) directly covers part of that need.
        total_need = income_need + float(charity_need)
        from_savings_needed = max(0.0, total_need - float(qcd) - total_ss)

        qcd_from_rmd = min(float(qcd), total_rmd_this_year) if total_rmd_this_year > 0 else 0.0
        qcd_extra = max(0.0, float(qcd) - qcd_from_rmd)

        # Use RMDs (net of any QCD applied against the RMD) toward annual spending first.
        rmd_available_for_income = max(0.0, total_rmd_this_year - qcd_from_rmd)
        rmd_for_income = min(rmd_available_for_income, from_savings_needed)
        remaining_need = from_savings_needed - rmd_for_income

        # Regular spending withdrawals (simple heuristic like the main projection).
        from_taxable = min(remaining_need * 0.5, max(0.0, taxable - float(inputs.plan.minimum_cash_reserve)))
        from_roth_requested = min(remaining_need * 0.3, roth)
        roth_penalty_tax = 0.0
        if bool(inputs.roth_rules.enabled) and from_roth_requested > 0:
            household_age_years = min(spouse1_age, spouse2_age)
            actual_from_roth, penalty_base = roth_ledger.withdraw(
                requested=from_roth_requested,
                year_index=yr,
                conversion_wait_years=int(inputs.roth_rules.conversion_wait_years),
                qualified_age_years=int(inputs.roth_rules.qualified_age_years),
                household_age_years=int(household_age_years),
                policy=str(inputs.roth_rules.policy),
            )
            from_roth = min(float(actual_from_roth), roth)
            shortfall = max(0.0, float(from_roth_requested - from_roth))
            if shortfall > 0:
                # Cover any prevented Roth spending from IRA.
                remaining_need += shortfall

            if penalty_base > 0:
                roth_penalty_tax += float(inputs.roth_rules.penalty_rate) * float(penalty_base)
        else:
            from_roth = from_roth_requested

        from_ira_spending = max(0.0, remaining_need - from_taxable - from_roth)

        # Home purchase drawdown (prioritize taxable above reserve, then Roth, then IRA).
        home_from_taxable = 0.0
        home_from_roth = 0.0
        home_from_ira = 0.0
        if home_cash_need > 0:
            year["home_purchase"] = True
            available_cash = max(0.0, taxable - float(inputs.plan.minimum_cash_reserve) - from_taxable)
            home_from_taxable = min(home_cash_need, available_cash)
            remaining_home = home_cash_need - home_from_taxable
            if remaining_home > 0:
                home_from_roth_requested = min(remaining_home, max(0.0, roth - from_roth))
                if bool(inputs.roth_rules.enabled) and home_from_roth_requested > 0:
                    household_age_years = min(spouse1_age, spouse2_age)
                    actual_home_from_roth, penalty_base = roth_ledger.withdraw(
                        requested=home_from_roth_requested,
                        year_index=yr,
                        conversion_wait_years=int(inputs.roth_rules.conversion_wait_years),
                        qualified_age_years=int(inputs.roth_rules.qualified_age_years),
                        household_age_years=int(household_age_years),
                        policy=str(inputs.roth_rules.policy),
                    )
                    home_from_roth = min(float(actual_home_from_roth), max(0.0, roth - from_roth))
                    remaining_home -= home_from_roth

                    if penalty_base > 0:
                        roth_penalty_tax += float(inputs.roth_rules.penalty_rate) * float(penalty_base)
                else:
                    home_from_roth = home_from_roth_requested
                    remaining_home -= home_from_roth
            if remaining_home > 0:
                home_from_ira = remaining_home
            year["home_from_taxable"] = home_from_taxable
            year["home_from_roth"] = home_from_roth
            year["home_from_ira"] = home_from_ira
        else:
            year["home_purchase"] = False

        taxable_ira_withdrawal = max(0.0, total_rmd_this_year - qcd_from_rmd) + from_ira_spending + home_from_ira
        total_ira_outflow = total_rmd_this_year + from_ira_spending + home_from_ira + qcd_extra

        # Compute SS taxable (without conversion) and base taxable income.
        ss_taxable_no_conv = taxable_social_security(
            total_benefits=total_ss,
            other_income=taxable_ira_withdrawal,
            filing_status=filing_status,
        )
        base_taxable_income = max(0.0, ss_taxable_no_conv + taxable_ira_withdrawal - float(standard_deduction))

        # Conversions (tax-aware, still simplified: aim for ≤24% by default).
        conversion = 0.0
        conversion_tax = 0.0
        if yr < int(conversion_years) and float(max_annual_conv) > 0:
            # Available to pay conversion tax from taxable after spending + home.
            available_for_conv_tax = max(
                0.0,
                taxable
                - float(inputs.plan.minimum_cash_reserve)
                - from_taxable
                - home_from_taxable,
            )

            mr = marginal_rate_ordinary_income(
                taxable_income=base_taxable_income,
                tax_year=calendar_year,
                filing_status=filing_status,
            )

            try:
                ceiling_24 = get_bracket_ceiling(tax_year=calendar_year, filing_status=filing_status, rate=0.24)
            except Exception:
                ceiling_24 = 383_900.0

            room_in_24 = max(0.0, float(ceiling_24) - base_taxable_income)
            max_affordable = available_for_conv_tax / mr if mr > 0 else 0.0

            conversion = min(float(max_annual_conv), room_in_24, max_affordable, max(0.0, ira - total_ira_outflow))
            conversion = max(0.0, conversion)

            if conversion > 0:
                ss_taxable_with_conv = taxable_social_security(
                    total_benefits=total_ss,
                    other_income=taxable_ira_withdrawal + conversion,
                    filing_status=filing_status,
                )
                taxable_income_with_conv = max(
                    0.0,
                    ss_taxable_with_conv + taxable_ira_withdrawal + conversion - float(standard_deduction),
                )
                taxable_income_no_conv = max(
                    0.0,
                    ss_taxable_no_conv + taxable_ira_withdrawal - float(standard_deduction),
                )
                conversion_tax = calculate_tax_ordinary_income(
                    taxable_income=taxable_income_with_conv,
                    tax_year=calendar_year,
                    filing_status=filing_status,
                ) - calculate_tax_ordinary_income(
                    taxable_income=taxable_income_no_conv,
                    tax_year=calendar_year,
                    filing_status=filing_status,
                )
                total_conversions += conversion

        # Income tax after conversion.
        ss_taxable_final = taxable_social_security(
            total_benefits=total_ss,
            other_income=taxable_ira_withdrawal + conversion,
            filing_status=filing_status,
        )
        total_taxable_income = max(
            0.0,
            ss_taxable_final + taxable_ira_withdrawal + conversion - float(standard_deduction),
        )
        income_tax = calculate_tax_ordinary_income(
            taxable_income=total_taxable_income,
            tax_year=calendar_year,
            filing_status=filing_status,
        )
        mr_for_grossup = marginal_rate_ordinary_income(
            taxable_income=total_taxable_income,
            tax_year=calendar_year,
            filing_status=filing_status,
        )

        # Allocate portion of income tax to RMD for reporting.
        rmd_taxable = max(0.0, total_rmd_this_year - qcd_from_rmd)
        rmd_tax = (income_tax * (rmd_taxable / taxable_ira_withdrawal)) if taxable_ira_withdrawal > 0 else 0.0
        total_rmd_tax += rmd_tax

        # NIIT: approximate *realized* net investment income (NII) from taxable investment return.
        taxable_balance_for_nii = max(0.0, float(year.get("taxable_start", taxable)) - float(from_taxable) - float(home_from_taxable))
        investment_income = 0.0
        if bool(getattr(inputs, "niit", None)) and bool(inputs.niit.enabled):
            nii_fraction = float(getattr(inputs.niit, "nii_fraction_of_return", 0.70))
            realization = float(getattr(inputs.niit, "realization_fraction", 0.60))
            investment_income = max(0.0, taxable_balance_for_nii * float(inputs.assumptions.taxable_return) * nii_fraction * realization)

        # Medicare costs (base Part B premium + IRMAA add-ons).
        irmaa_cost = 0.0
        medicare_part_b_base_cost = 0.0
        magi_current_year = float(taxable_ira_withdrawal) + float(conversion) + float(ss_taxable_final) + float(investment_income)
        magi_by_calendar_year[calendar_year] = magi_current_year

        covered_people_cfg = getattr(inputs.medicare, "covered_people", None)
        covered_people = int(covered_people_cfg) if covered_people_cfg is not None else (2 if filing_status == "MFJ" else 1)

        if bool(getattr(inputs.medicare, "part_b_base_premium_enabled", False)):
            part_b_base = get_part_b_base_premium_monthly(premium_year=calendar_year)
            medicare_part_b_base_cost = float(part_b_base) * 12.0 * float(covered_people)
            total_medicare_part_b_base_premium_cost += medicare_part_b_base_cost

        if bool(inputs.medicare.irmaa_enabled):
            lookback_magi = float(magi_by_calendar_year.get(calendar_year - 2, magi_current_year))
            part_b_add, part_d_add = get_irmaa_addons_monthly(
                premium_year=calendar_year,
                filing_status=filing_status,
                magi=lookback_magi,
            )
            irmaa_cost = (part_b_add + part_d_add) * 12.0 * float(covered_people)
            total_irmaa_cost += irmaa_cost

        state_tax = 0.0
        if bool(getattr(inputs, "state_tax", None)) and bool(inputs.state_tax.enabled) and float(inputs.state_tax.rate) > 0:
            base = str(getattr(inputs.state_tax, "base", "agi"))
            base_amount = magi_current_year if base == "agi" else float(total_taxable_income)
            state_tax = float(inputs.state_tax.rate) * max(0.0, float(base_amount))
            total_state_tax += state_tax

        niit_tax = 0.0
        if bool(getattr(inputs, "niit", None)) and bool(inputs.niit.enabled):
            niit_tax = calculate_niit(
                magi=magi_current_year,
                net_investment_income=investment_income,
                filing_status=filing_status,
            )

        if bool(inputs.roth_rules.enabled) and conversion > 0:
            roth_ledger.deposit_conversion(amount=conversion, year_index=yr)

        # Update balances (withdrawals + conversion).
        ira -= total_ira_outflow
        ira -= conversion
        roth += conversion

        taxable -= from_taxable
        taxable -= home_from_taxable
        roth -= from_roth
        roth -= home_from_roth

        # Pay taxes/expenses.
        taxable, ira = pay_tax(
            taxable=taxable,
            ira=ira,
            tax_due=conversion_tax,
            source=str(tax_policy.conversion_tax_payment_source),
            minimum_cash_reserve=float(inputs.plan.minimum_cash_reserve),
            marginal_rate=mr_for_grossup,
        )
        taxable, ira = pay_tax(
            taxable=taxable,
            ira=ira,
            tax_due=income_tax,
            source=str(tax_policy.income_tax_payment_source),
            minimum_cash_reserve=float(inputs.plan.minimum_cash_reserve),
            marginal_rate=mr_for_grossup,
        )
        if state_tax > 0:
            taxable, ira = pay_tax(
                taxable=taxable,
                ira=ira,
                tax_due=state_tax,
                source=str(tax_policy.income_tax_payment_source),
                minimum_cash_reserve=float(inputs.plan.minimum_cash_reserve),
                marginal_rate=mr_for_grossup,
            )
        if niit_tax > 0:
            taxable, ira = pay_tax(
                taxable=taxable,
                ira=ira,
                tax_due=niit_tax,
                source=str(tax_policy.income_tax_payment_source),
                minimum_cash_reserve=float(inputs.plan.minimum_cash_reserve),
                marginal_rate=mr_for_grossup,
            )
        if irmaa_cost > 0:
            taxable, ira = pay_tax(
                taxable=taxable,
                ira=ira,
                tax_due=irmaa_cost,
                source="taxable",
                minimum_cash_reserve=float(inputs.plan.minimum_cash_reserve),
                marginal_rate=mr_for_grossup,
            )

        if medicare_part_b_base_cost > 0:
            taxable, ira = pay_tax(
                taxable=taxable,
                ira=ira,
                tax_due=medicare_part_b_base_cost,
                source="taxable",
                minimum_cash_reserve=float(inputs.plan.minimum_cash_reserve),
                marginal_rate=mr_for_grossup,
            )

        if roth_penalty_tax > 0:
            taxable, ira = pay_tax(
                taxable=taxable,
                ira=ira,
                tax_due=float(roth_penalty_tax),
                source=str(tax_policy.income_tax_payment_source),
                minimum_cash_reserve=float(inputs.plan.minimum_cash_reserve),
                marginal_rate=mr_for_grossup,
            )

        year["rmd"] = total_rmd_this_year
        year["rmd_tax"] = rmd_tax
        year["conversion"] = conversion
        year["conv_tax"] = conversion_tax
        year["income_tax"] = income_tax
        year["state_tax"] = state_tax
        year["irmaa_cost"] = irmaa_cost
        year["medicare_part_b_base_premium_cost"] = medicare_part_b_base_cost
        year["niit_tax"] = niit_tax
        year["roth_penalty_tax"] = float(roth_penalty_tax)
        year["magi"] = magi_current_year
        year["investment_income"] = investment_income

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
        total_irmaa_cost=total_irmaa_cost,
        total_medicare_part_b_base_premium_cost=total_medicare_part_b_base_premium_cost,
        total_state_tax=total_state_tax,
        after_tax=after_tax,
        legacy=legacy,
        yearly_data=tuple(yearly_data),
    )
