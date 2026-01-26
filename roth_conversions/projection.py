from __future__ import annotations

from typing import Optional, Sequence

from .models import HouseholdInputs, ProjectionResult, ProjectionYear, Strategy, as_float_seq, clamp_series
from .rmd import required_minimum_distribution
from .social_security import taxable_social_security
from .tax import calculate_tax_federal_ltcg_qd_simple, marginal_rate_ordinary_income
from .tax_tables import get_bracket_ceiling, get_standard_deduction
from .irmaa_tables import get_irmaa_addons_monthly
from .medicare_part_b_tables import get_part_b_base_premium_monthly
from .withdrawal_policy import pay_tax
from .npv import npv
from .heirs import simulate_inherited_distribution_after_tax, simulate_inherited_roth_after_tax
from .niit import calculate_niit
from .roth_rules import RothLedger
from .ira_basis import allocate_ira_basis_pro_rata


STANDARD_DEDUCTION_MFJ_APPROX_2025 = 30_000.0


def project_with_tax_tracking(
    *,
    inputs: HouseholdInputs,
    strategy: Strategy,
    horizon_years: int = 25,
    standard_deduction_mfj: float = STANDARD_DEDUCTION_MFJ_APPROX_2025,
    ira_returns: Optional[Sequence[float]] = None,
    roth_returns: Optional[Sequence[float]] = None,
    taxable_returns: Optional[Sequence[float]] = None,
    inflation_rates: Optional[Sequence[float]] = None,
) -> ProjectionResult:
    """Refactor of notebook `project_with_tax_tracking` (cell_01).

    - No globals: everything is derived from `inputs` + `strategy`.
    - Returns typed rows suitable for reporting or DataFrame conversion.
    """

    if horizon_years <= 0:
        raise ValueError("horizon_years must be > 0")

    ira_returns = clamp_series(as_float_seq(ira_returns), horizon_years=horizon_years, name="ira_returns")
    roth_returns = clamp_series(as_float_seq(roth_returns), horizon_years=horizon_years, name="roth_returns")
    taxable_returns = clamp_series(as_float_seq(taxable_returns), horizon_years=horizon_years, name="taxable_returns")
    inflation_rates = clamp_series(as_float_seq(inflation_rates), horizon_years=horizon_years, name="inflation_rates")

    ira = float(inputs.total_pretax)
    roth = float(inputs.total_roth)
    taxable = float(inputs.joint.taxable_accounts)
    ira_basis = float(getattr(inputs.joint, "ira_after_tax_basis", 0.0))

    roth_ledger = RothLedger(basis_remaining=float(roth), buckets=[])

    base_filing_status = str(inputs.household.tax_filing_status)
    tax_policy = inputs.tax_payment_policy
    widow_event = inputs.widow_event
    charity = inputs.charity
    heirs = inputs.heirs

    cumulative_conv_tax = 0.0
    cumulative_rmd_tax = 0.0
    cumulative_irmaa_cost = 0.0
    cumulative_medicare_part_b_cost = 0.0
    cumulative_niit_tax = 0.0
    cumulative_roth_penalty_tax = 0.0
    cumulative_state_tax = 0.0
    total_conversions = 0.0
    total_rmds = 0.0

    discount_rate = float(inputs.household.discount_rate)
    inflation_multiplier = 1.0
    yearly: list[ProjectionYear] = []

    magi_by_calendar_year: dict[int, float] = {}

    for yr in range(horizon_years):
        spouse1_age = int(inputs.spouse1.age) + yr
        spouse2_age = int(inputs.spouse2.age) + yr
        calendar_year = int(inputs.household.start_year) + yr

        widow_active = bool(widow_event.enabled) and widow_event.widow_year is not None and calendar_year >= int(widow_event.widow_year)
        filing_status = "Single" if widow_active else base_filing_status

        # Use pinned tax table data when available; fall back to the historical constant only
        # if the filing status isn't supported by the pinned tables.
        try:
            standard_deduction = get_standard_deduction(tax_year=calendar_year, filing_status=filing_status)
        except Exception:
            # Backwards compatibility: old behavior assumed MFJ.
            standard_deduction = float(standard_deduction_mfj)

        itemized_deduction = 0.0
        if bool(getattr(inputs, "itemized_deductions", None)) and bool(inputs.itemized_deductions.enabled):
            itemized_deduction = float(inputs.itemized_deductions.itemized_deductions_annual) * inflation_multiplier

        deduction = max(float(standard_deduction), float(itemized_deduction))

        ira_r = float(ira_returns[yr]) if ira_returns is not None else float(inputs.assumptions.ira_return)
        roth_r = float(roth_returns[yr]) if roth_returns is not None else float(inputs.assumptions.roth_return)
        taxable_r = float(taxable_returns[yr]) if taxable_returns is not None else float(inputs.assumptions.taxable_return)
        infl_r = float(inflation_rates[yr]) if inflation_rates is not None else float(inputs.assumptions.inflation_rate)

        # Social security
        ss1 = float(inputs.spouse1.ss_annual) if yr >= inputs.years_to_spouse1_ss else 0.0
        ss2 = float(inputs.spouse2.ss_annual) if yr >= inputs.years_to_spouse2_ss else 0.0
        # Widow modeling (simple): survivor benefit is the larger of the two benefits.
        total_ss = max(ss1, ss2) if widow_active else (ss1 + ss2)

        # IRMAA uses (typically) 2-year lookback MAGI; we approximate MAGI as AGI
        # from this model (IRA withdrawals + conversions + taxable SS).
        # We'll compute MAGI after we compute taxable SS for the final income picture.
        irmaa_cost = 0.0
        medicare_part_b_base_cost = 0.0

        # NIIT: approximate net investment income (NII) from the taxable account return.
        # Important: portfolio return != NII; we approximate realized NII using configurable scalars.
        investment_income = 0.0

        income_need_multiplier = float(widow_event.income_need_multiplier) if widow_active else 1.0
        income_need = float(inputs.plan.annual_income_need) * inflation_multiplier * income_need_multiplier

        charity_need = 0.0
        qcd = 0.0
        if bool(charity.enabled) and float(charity.annual_amount) > 0:
            charity_need = float(charity.annual_amount) * inflation_multiplier
            if bool(charity.use_qcd):
                eligible_age = float(charity.qcd_eligible_age)
                eligible = (float(spouse1_age) >= eligible_age) or (float(spouse2_age) >= eligible_age)
                if eligible:
                    covered_people = 2 if filing_status == "MFJ" else 1
                    cap = float(charity.qcd_annual_cap_per_person) * float(covered_people)
                    qcd = min(charity_need, cap, max(0.0, ira))

        # Spending need includes charitable giving; QCD (if any) is treated as covering part of that need.
        total_need = income_need + charity_need
        from_savings_needed = max(0.0, total_need - qcd - total_ss)

        # RMDs (notebook splits IRA 33/67)
        spouse1_rmd = required_minimum_distribution(ira * 0.33, spouse1_age)
        spouse2_rmd = required_minimum_distribution(ira * 0.67, spouse2_age)
        total_rmd = spouse1_rmd + spouse2_rmd
        total_rmds += total_rmd

        qcd_from_rmd = min(qcd, total_rmd) if total_rmd > 0 else 0.0
        qcd_extra = max(0.0, qcd - qcd_from_rmd)

        # Pro-rata basis allocation: treat QCD as an IRA distribution that can consume basis.
        # QCD is excluded from income regardless, so we only use it to reduce remaining basis.
        ira_after_qcd = ira
        if ira_basis > 0.0 and qcd > 0.0 and ira > 0.0:
            _, _, ira_basis = allocate_ira_basis_pro_rata(
                ira_balance=ira,
                basis_remaining=ira_basis,
                amount=qcd,
            )
            ira_after_qcd = max(0.0, ira - qcd)

        rmd_available_for_income = max(0.0, total_rmd - qcd_from_rmd)
        rmd_for_income = min(rmd_available_for_income, from_savings_needed)
        remaining_need = from_savings_needed - rmd_for_income

        # Withdrawals
        from_taxable = min(remaining_need * 0.5, max(0.0, taxable - float(inputs.plan.minimum_cash_reserve)))
        from_roth_requested = min(remaining_need * 0.3, roth)
        roth_penalty_tax = 0.0
        if bool(inputs.roth_rules.enabled) and from_roth_requested > 0:
            # Whole-year approximation: if both spouses are modeled, use the younger as the conservative age.
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
            remaining_need += shortfall

            if penalty_base > 0:
                roth_penalty_tax = float(inputs.roth_rules.penalty_rate) * float(penalty_base)
        else:
            from_roth = from_roth_requested

        from_ira_extra = max(0.0, remaining_need - from_taxable - from_roth)

        ira_withdrawal_gross = max(0.0, total_rmd - qcd_from_rmd) + from_ira_extra
        if ira_basis > 0.0 and ira_withdrawal_gross > 0.0 and ira_after_qcd > 0.0:
            taxable_ira_withdrawal, _, ira_basis = allocate_ira_basis_pro_rata(
                ira_balance=ira_after_qcd,
                basis_remaining=ira_basis,
                amount=ira_withdrawal_gross,
            )
        else:
            taxable_ira_withdrawal = ira_withdrawal_gross

        ira_after_qcd_and_withdrawals = max(0.0, ira_after_qcd - ira_withdrawal_gross)
        total_ira_outflow = total_rmd + from_ira_extra + qcd_extra

        taxable_balance_for_nii = max(0.0, taxable - from_taxable)
        if bool(getattr(inputs, "niit", None)) and bool(inputs.niit.enabled):
            nii_fraction = float(getattr(inputs.niit, "nii_fraction_of_return", 0.70))
            realization = float(getattr(inputs.niit, "realization_fraction", 0.60))
            investment_income = max(0.0, taxable_balance_for_nii * taxable_r * nii_fraction * realization)

        # Compute SS taxable using IRS provisional income rules.
        # Note: taxable SS depends on other income (IRA withdrawals, conversions), so we
        # compute "without conversion" and "with conversion" versions when needed.
        ss_taxable_no_conv = taxable_social_security(
            total_benefits=total_ss,
            other_income=taxable_ira_withdrawal,
            filing_status=filing_status,
        )

        qualified_dividends = 0.0
        long_term_capital_gains = 0.0
        if bool(getattr(inputs, "preferential_income", None)):
            qualified_dividends = float(inputs.preferential_income.qualified_dividends_annual) * inflation_multiplier
            long_term_capital_gains = float(inputs.preferential_income.long_term_capital_gains_annual) * inflation_multiplier

        # Ordinary taxable income excludes preferential income.
        base_taxable_income = max(
            0.0,
            (ss_taxable_no_conv + taxable_ira_withdrawal + qualified_dividends + long_term_capital_gains) - float(deduction),
        )
        base_pref_taxable = min(max(0.0, qualified_dividends + long_term_capital_gains), base_taxable_income)
        base_ordinary_taxable_income = max(0.0, base_taxable_income - base_pref_taxable)

        # Conversions
        conversion = 0.0
        taxable_conversion_income = 0.0
        conversion_tax = 0.0
        if yr < int(strategy.conversion_years) and float(strategy.annual_conversion) > 0:
            available_for_conv_tax = max(0.0, taxable - float(inputs.plan.minimum_cash_reserve) - from_taxable)

            # Constrain conversions to stay within a chosen bracket ceiling.
            # We use pinned ceilings when available (by filing status + calendar year).
            try:
                bracket_24_ceiling = get_bracket_ceiling(tax_year=calendar_year, filing_status=filing_status, rate=0.24)
                bracket_32_ceiling = get_bracket_ceiling(tax_year=calendar_year, filing_status=filing_status, rate=0.32)
            except Exception:
                # Backwards compatibility with notebook constants (MFJ 2024 values).
                bracket_24_ceiling = 383_900.0
                bracket_32_ceiling = 487_450.0

            room_in_brackets = max(
                0.0,
                (bracket_32_ceiling if strategy.allow_32_bracket else bracket_24_ceiling) - base_ordinary_taxable_income,
            )

            # Notebook used 0.28 here for max_affordable
            max_affordable = (available_for_conv_tax / 0.28) if available_for_conv_tax > 0 else 0.0

            # If the household has after-tax basis in IRA, only the taxable portion counts toward brackets.
            taxable_fraction = 1.0
            if ira_after_qcd_and_withdrawals > 0.0 and ira_basis > 0.0:
                taxable_fraction = max(0.0, (ira_after_qcd_and_withdrawals - ira_basis) / ira_after_qcd_and_withdrawals)

            gross_room = room_in_brackets / taxable_fraction if taxable_fraction > 0.0 else max(0.0, ira_after_qcd_and_withdrawals)
            gross_affordable = max_affordable / taxable_fraction if taxable_fraction > 0.0 else max(0.0, ira_after_qcd_and_withdrawals)

            conversion = min(
                float(strategy.annual_conversion),
                gross_room,
                gross_affordable,
                max(0.0, ira_after_qcd_and_withdrawals),
            )
            conversion = max(0.0, conversion)

            if conversion > 0:
                taxable_conversion_income = conversion
                if ira_basis > 0.0 and conversion > 0.0 and ira_after_qcd_and_withdrawals > 0.0:
                    taxable_conversion_income, _, ira_basis = allocate_ira_basis_pro_rata(
                        ira_balance=ira_after_qcd_and_withdrawals,
                        basis_remaining=ira_basis,
                        amount=conversion,
                    )

                ss_taxable_with_conv = taxable_social_security(
                    total_benefits=total_ss,
                    other_income=taxable_ira_withdrawal + taxable_conversion_income,
                    filing_status=filing_status,
                )
                taxable_income_with_conv = max(
                    0.0, ss_taxable_with_conv + taxable_ira_withdrawal + taxable_conversion_income - float(standard_deduction)
                )
                taxable_income_no_conv = max(0.0, ss_taxable_no_conv + taxable_ira_withdrawal - float(standard_deduction))

                # Full tax difference, including the effect of conversions pushing LTCG/QD into higher rate brackets.
                conversion_tax = calculate_tax_federal_ltcg_qd_simple(
                    ordinary_income=float(ss_taxable_with_conv) + float(taxable_ira_withdrawal) + float(taxable_conversion_income),
                    qualified_dividends=float(qualified_dividends),
                    long_term_capital_gains=float(long_term_capital_gains),
                    deduction=float(deduction),
                    tax_year=calendar_year,
                    filing_status=filing_status,
                ) - calculate_tax_federal_ltcg_qd_simple(
                    ordinary_income=float(ss_taxable_no_conv) + float(taxable_ira_withdrawal),
                    qualified_dividends=float(qualified_dividends),
                    long_term_capital_gains=float(long_term_capital_gains),
                    deduction=float(deduction),
                    tax_year=calendar_year,
                    filing_status=filing_status,
                )
                total_conversions += conversion
                cumulative_conv_tax += conversion_tax

        # Track conversions for Roth 5-year rule approximations.
        if bool(inputs.roth_rules.enabled) and conversion > 0:
            roth_ledger.deposit_conversion(amount=conversion, year_index=yr)

        # Income tax & allocate portion to RMD
        # Income tax after conversion decision.
        ss_taxable_final = taxable_social_security(
            total_benefits=total_ss,
            other_income=taxable_ira_withdrawal + taxable_conversion_income,
            filing_status=filing_status,
        )
        income_tax = calculate_tax_federal_ltcg_qd_simple(
            ordinary_income=float(ss_taxable_final) + float(taxable_ira_withdrawal) + float(taxable_conversion_income),
            qualified_dividends=float(qualified_dividends),
            long_term_capital_gains=float(long_term_capital_gains),
            deduction=float(deduction),
            tax_year=calendar_year,
            filing_status=filing_status,
        )

        total_taxable_income = max(
            0.0,
            (ss_taxable_final + taxable_ira_withdrawal + taxable_conversion_income + qualified_dividends + long_term_capital_gains) - float(deduction),
        )

        state_tax = 0.0
        if bool(getattr(inputs, "state_tax", None)) and bool(inputs.state_tax.enabled) and float(inputs.state_tax.rate) > 0:
            base = str(getattr(inputs.state_tax, "base", "agi"))
            # Our best available internal approximation of AGI/MAGI is:
            # IRA withdrawals + conversions + taxable SS + (realized) investment income.
            agi_approx = (
                float(taxable_ira_withdrawal)
                + float(taxable_conversion_income)
                + float(ss_taxable_final)
                + float(qualified_dividends)
                + float(long_term_capital_gains)
                + float(investment_income)
            )
            base_amount = agi_approx if base == "agi" else float(total_taxable_income)
            state_tax = float(inputs.state_tax.rate) * max(0.0, float(base_amount))
            cumulative_state_tax += state_tax

        mr_for_grossup = marginal_rate_ordinary_income(
            taxable_income=total_taxable_income,
            tax_year=calendar_year,
            filing_status=filing_status,
        )

        # Persist MAGI estimate for lookback calculations.
        magi_current_year = (
            float(taxable_ira_withdrawal)
            + float(taxable_conversion_income)
            + float(ss_taxable_final)
            + float(qualified_dividends)
            + float(long_term_capital_gains)
            + float(investment_income)
        )
        magi_by_calendar_year[calendar_year] = magi_current_year

        niit_tax = 0.0
        if bool(getattr(inputs, "niit", None)) and bool(inputs.niit.enabled):
            niit_tax = calculate_niit(
                magi=magi_current_year,
                net_investment_income=investment_income,
                filing_status=filing_status,
            )
            cumulative_niit_tax += niit_tax

        if roth_penalty_tax > 0:
            cumulative_roth_penalty_tax += float(roth_penalty_tax)

        covered_people_cfg = getattr(inputs.medicare, "covered_people", None)
        covered_people = int(covered_people_cfg) if covered_people_cfg is not None else (2 if filing_status == "MFJ" else 1)

        if bool(getattr(inputs.medicare, "part_b_base_premium_enabled", False)):
            part_b_base = get_part_b_base_premium_monthly(premium_year=calendar_year)
            medicare_part_b_base_cost = float(part_b_base) * 12.0 * float(covered_people)
            cumulative_medicare_part_b_cost += medicare_part_b_base_cost

        if bool(inputs.medicare.irmaa_enabled):
            lookback_year = calendar_year - 2
            lookback_magi = float(magi_by_calendar_year.get(lookback_year, magi_current_year))
            part_b_add, part_d_add = get_irmaa_addons_monthly(
                premium_year=calendar_year,
                filing_status=filing_status,
                magi=lookback_magi,
            )
            irmaa_cost = (part_b_add + part_d_add) * 12.0 * float(covered_people)
            cumulative_irmaa_cost += irmaa_cost

        rmd_taxable = max(0.0, total_rmd - qcd_from_rmd)
        if taxable_ira_withdrawal > 0:
            rmd_share = rmd_taxable / taxable_ira_withdrawal
            rmd_tax = income_tax * rmd_share
        else:
            rmd_tax = 0.0

        cumulative_rmd_tax += rmd_tax
        cumulative_total_tax = (
            cumulative_conv_tax
            + cumulative_rmd_tax
            + cumulative_niit_tax
            + cumulative_roth_penalty_tax
            + cumulative_state_tax
        )

        # Update balances
        ira -= total_ira_outflow
        ira -= conversion
        roth += conversion
        roth -= from_roth
        taxable -= from_taxable

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

        # Roth early-withdrawal penalty treated as an annual tax/expense.
        if roth_penalty_tax > 0:
            taxable, ira = pay_tax(
                taxable=taxable,
                ira=ira,
                tax_due=float(roth_penalty_tax),
                source=str(tax_policy.income_tax_payment_source),
                minimum_cash_reserve=float(inputs.plan.minimum_cash_reserve),
                marginal_rate=mr_for_grossup,
            )

        # Treat IRMAA as an annual expense paid from taxable (then IRA spillover).
        if irmaa_cost > 0:
            taxable, ira = pay_tax(
                taxable=taxable,
                ira=ira,
                tax_due=irmaa_cost,
                source="taxable",
                minimum_cash_reserve=float(inputs.plan.minimum_cash_reserve),
                marginal_rate=mr_for_grossup,
            )

        # Treat Part B base premium as an annual expense paid from taxable (then IRA spillover).
        if medicare_part_b_base_cost > 0:
            taxable, ira = pay_tax(
                taxable=taxable,
                ira=ira,
                tax_due=medicare_part_b_base_cost,
                source="taxable",
                minimum_cash_reserve=float(inputs.plan.minimum_cash_reserve),
                marginal_rate=mr_for_grossup,
            )

        ira *= (1.0 + ira_r)
        roth *= (1.0 + roth_r)
        taxable *= (1.0 + taxable_r)

        ira = max(0.0, ira)
        roth = max(0.0, roth)
        taxable = max(0.0, taxable)

        yearly.append(
            ProjectionYear(
                year=yr + 1,
                calendar_year=calendar_year,
                spouse1_age=spouse1_age,
                spouse2_age=spouse2_age,
                ss_income=total_ss,
                rmd=total_rmd,
                ira_withdrawal=taxable_ira_withdrawal,
                from_taxable=from_taxable,
                from_roth=from_roth,
                conversion=conversion,
                conversion_tax=conversion_tax,
                income_tax=income_tax,
                ira_end=ira,
                roth_end=roth,
                taxable_end=taxable,
                cumulative_conv_tax=cumulative_conv_tax,
                cumulative_rmd_tax=cumulative_rmd_tax,
                cumulative_total_tax=cumulative_total_tax,
                irmaa_cost=irmaa_cost,
                niit_tax=niit_tax,
                roth_penalty_tax=float(roth_penalty_tax),
                magi=magi_current_year,
                investment_income=investment_income,
                income_need=income_need,
                inflation_multiplier=inflation_multiplier,
                qcd=qcd,
                charity_need=charity_need,
                medicare_part_b_base_premium_cost=medicare_part_b_base_cost,
                state_tax=state_tax,
            )
        )

        inflation_multiplier *= (1.0 + infl_r)

    after_tax = ira * 0.75 + roth + taxable * 0.92
    legacy = ira * (1.0 - 0.28) + roth + taxable * 0.95

    heirs_after_tax = 0.0
    if bool(heirs.enabled):
        heirs_years = int(heirs.distribution_years)
        heirs_from_ira = simulate_inherited_distribution_after_tax(
            pretax_balance=ira,
            distribution_years=heirs_years,
            pretax_return=float(inputs.assumptions.ira_return),
            beneficiary_tax_rate=float(heirs.heir_tax_rate),
            beneficiary_taxable_return=float(inputs.assumptions.taxable_return),
        )
        heirs_from_roth = simulate_inherited_roth_after_tax(
            roth_balance=roth,
            distribution_years=heirs_years,
            roth_return=float(inputs.assumptions.roth_return),
            beneficiary_taxable_return=float(inputs.assumptions.taxable_return),
        )
        heirs_after_tax = heirs_from_ira + heirs_from_roth + taxable * 0.95

    end_inflation_multiplier = yearly[-1].inflation_multiplier if yearly else 1.0
    after_tax_today = after_tax / end_inflation_multiplier
    legacy_today = legacy / end_inflation_multiplier
    heirs_after_tax_today = heirs_after_tax / end_inflation_multiplier

    spending_today_series = [float(y.income_need) / float(y.inflation_multiplier) for y in yearly]
    taxes_today_series = [
        (
            float(y.income_tax)
            + float(y.conversion_tax)
            + float(getattr(y, "state_tax", 0.0))
            + float(y.irmaa_cost)
            + float(getattr(y, "medicare_part_b_base_premium_cost", 0.0))
            + float(y.niit_tax)
            + float(y.roth_penalty_tax)
        )
        / float(y.inflation_multiplier)
        for y in yearly
    ]

    npv_spending_today = npv(spending_today_series, discount_rate=discount_rate)
    npv_taxes_today = npv(taxes_today_series, discount_rate=discount_rate)

    return ProjectionResult(
        strategy=strategy,
        total_conversions=total_conversions,
        total_conv_tax=cumulative_conv_tax,
        total_rmds=total_rmds,
        total_rmd_tax=cumulative_rmd_tax,
        total_lifetime_tax=cumulative_conv_tax
        + cumulative_rmd_tax
        + cumulative_niit_tax
        + cumulative_roth_penalty_tax
        + cumulative_state_tax,
        total_roth_penalty_tax=cumulative_roth_penalty_tax,
        after_tax=after_tax,
        legacy=legacy,
        yearly=tuple(yearly),
        total_irmaa_cost=cumulative_irmaa_cost,
        total_medicare_part_b_base_premium_cost=cumulative_medicare_part_b_cost,
        total_niit_tax=cumulative_niit_tax,
        total_state_tax=cumulative_state_tax,
        after_tax_today=after_tax_today,
        legacy_today=legacy_today,
        npv_spending_today=npv_spending_today,
        npv_taxes_today=npv_taxes_today,
        heirs_after_tax=heirs_after_tax,
        heirs_after_tax_today=heirs_after_tax_today,
    )


def project_path(
    *,
    inputs: HouseholdInputs,
    annual_conversion: float,
    conversion_years: int,
    path_name: str = "",
    horizon_years: int = 25,
    standard_deduction_mfj: float = STANDARD_DEDUCTION_MFJ_APPROX_2025,
) -> dict:
    """Refactor of notebook `project_path` (cell_10).

    Returns a dict matching the notebook's keys closely for backwards compatibility.
    """

    ira = float(inputs.total_pretax)
    roth = float(inputs.total_roth)
    taxable = float(inputs.joint.taxable_accounts)
    ira_basis = float(getattr(inputs.joint, "ira_after_tax_basis", 0.0))

    roth_ledger = RothLedger(basis_remaining=float(roth), buckets=[])

    base_filing_status = str(inputs.household.tax_filing_status)
    tax_policy = inputs.tax_payment_policy
    widow_event = inputs.widow_event
    charity = inputs.charity
    heirs = inputs.heirs

    total_conversions = 0.0
    total_conversion_tax = 0.0
    total_rmds = 0.0
    total_rmd_tax = 0.0
    total_irmaa_cost = 0.0
    total_medicare_part_b_base_premium_cost = 0.0
    total_niit_tax = 0.0
    total_roth_penalty_tax = 0.0
    total_state_tax = 0.0

    yearly_details: list[dict] = []

    inflation_multiplier = 1.0

    magi_by_calendar_year: dict[int, float] = {}

    for yr in range(horizon_years):
        spouse1_age = int(inputs.spouse1.age) + yr
        spouse2_age = int(inputs.spouse2.age) + yr
        calendar_year = int(inputs.household.start_year) + yr

        widow_active = bool(widow_event.enabled) and widow_event.widow_year is not None and calendar_year >= int(widow_event.widow_year)
        filing_status = "Single" if widow_active else base_filing_status

        try:
            standard_deduction = get_standard_deduction(tax_year=calendar_year, filing_status=filing_status)
        except Exception:
            standard_deduction = float(standard_deduction_mfj)

        itemized_deduction = 0.0
        if bool(getattr(inputs, "itemized_deductions", None)) and bool(inputs.itemized_deductions.enabled):
            itemized_deduction = float(inputs.itemized_deductions.itemized_deductions_annual) * inflation_multiplier

        deduction = max(float(standard_deduction), float(itemized_deduction))

        ss1 = float(inputs.spouse1.ss_annual) if yr >= inputs.years_to_spouse1_ss else 0.0
        ss2 = float(inputs.spouse2.ss_annual) if yr >= inputs.years_to_spouse2_ss else 0.0
        total_ss = max(ss1, ss2) if widow_active else (ss1 + ss2)

        income_need_multiplier = float(widow_event.income_need_multiplier) if widow_active else 1.0
        income_need = float(inputs.plan.annual_income_need) * inflation_multiplier * income_need_multiplier

        charity_need = 0.0
        qcd = 0.0
        if bool(charity.enabled) and float(charity.annual_amount) > 0:
            charity_need = float(charity.annual_amount) * inflation_multiplier
            if bool(charity.use_qcd):
                eligible_age = float(charity.qcd_eligible_age)
                eligible = (float(spouse1_age) >= eligible_age) or (float(spouse2_age) >= eligible_age)
                if eligible:
                    covered_people = 2 if filing_status == "MFJ" else 1
                    cap = float(charity.qcd_annual_cap_per_person) * float(covered_people)
                    qcd = min(charity_need, cap, max(0.0, ira))

        total_need = income_need + charity_need
        from_savings_needed = max(0.0, total_need - qcd - total_ss)

        spouse1_rmd = required_minimum_distribution(ira * 0.33, spouse1_age)
        spouse2_rmd = required_minimum_distribution(ira * 0.67, spouse2_age)
        total_rmd = spouse1_rmd + spouse2_rmd
        total_rmds += total_rmd

        qcd_from_rmd = min(qcd, total_rmd) if total_rmd > 0 else 0.0
        qcd_extra = max(0.0, qcd - qcd_from_rmd)

        ira_after_qcd = ira
        if ira_basis > 0.0 and qcd > 0.0 and ira > 0.0:
            _, _, ira_basis = allocate_ira_basis_pro_rata(
                ira_balance=ira,
                basis_remaining=ira_basis,
                amount=qcd,
            )
            ira_after_qcd = max(0.0, ira - qcd)

        rmd_available_for_income = max(0.0, total_rmd - qcd_from_rmd)
        rmd_for_income = min(rmd_available_for_income, from_savings_needed)
        remaining_need = from_savings_needed - rmd_for_income

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
            remaining_need += shortfall
            if penalty_base > 0:
                roth_penalty_tax = float(inputs.roth_rules.penalty_rate) * float(penalty_base)
        else:
            from_roth = from_roth_requested

        from_ira_extra = max(0.0, remaining_need - from_taxable - from_roth)
        ira_withdrawal_gross = max(0.0, total_rmd - qcd_from_rmd) + from_ira_extra
        if ira_basis > 0.0 and ira_withdrawal_gross > 0.0 and ira_after_qcd > 0.0:
            taxable_ira_withdrawal, _, ira_basis = allocate_ira_basis_pro_rata(
                ira_balance=ira_after_qcd,
                basis_remaining=ira_basis,
                amount=ira_withdrawal_gross,
            )
        else:
            taxable_ira_withdrawal = ira_withdrawal_gross

        ira_after_qcd_and_withdrawals = max(0.0, ira_after_qcd - ira_withdrawal_gross)
        total_ira_outflow = total_rmd + from_ira_extra + qcd_extra

        taxable_balance_for_nii = max(0.0, taxable - from_taxable)
        investment_income = 0.0
        if bool(getattr(inputs, "niit", None)) and bool(inputs.niit.enabled):
            nii_fraction = float(getattr(inputs.niit, "nii_fraction_of_return", 0.70))
            realization = float(getattr(inputs.niit, "realization_fraction", 0.60))
            investment_income = max(0.0, taxable_balance_for_nii * float(inputs.assumptions.taxable_return) * nii_fraction * realization)

        ss_taxable_no_conv = taxable_social_security(
            total_benefits=total_ss,
            other_income=taxable_ira_withdrawal,
            filing_status=filing_status,
        )

        qualified_dividends = 0.0
        long_term_capital_gains = 0.0
        if bool(getattr(inputs, "preferential_income", None)):
            qualified_dividends = float(inputs.preferential_income.qualified_dividends_annual) * inflation_multiplier
            long_term_capital_gains = float(inputs.preferential_income.long_term_capital_gains_annual) * inflation_multiplier

        conversion = 0.0
        taxable_conversion_income = 0.0
        conversion_tax = 0.0
        if yr < int(conversion_years) and float(annual_conversion) > 0:
            available_for_conv_tax = max(0.0, taxable - float(inputs.plan.minimum_cash_reserve) - from_taxable)

            base_taxable_income = max(
                0.0,
                (ss_taxable_no_conv + taxable_ira_withdrawal + qualified_dividends + long_term_capital_gains) - float(deduction),
            )
            base_pref_taxable = min(max(0.0, qualified_dividends + long_term_capital_gains), base_taxable_income)
            base_ordinary_taxable_income = max(0.0, base_taxable_income - base_pref_taxable)
            mr = marginal_rate_ordinary_income(
                taxable_income=base_ordinary_taxable_income,
                tax_year=calendar_year,
                filing_status=filing_status,
            )

            try:
                ceiling_24 = get_bracket_ceiling(tax_year=calendar_year, filing_status=filing_status, rate=0.24)
            except Exception:
                ceiling_24 = 383_900.0

            room_in_24 = max(0.0, float(ceiling_24) - base_ordinary_taxable_income)
            max_affordable = available_for_conv_tax / mr if mr > 0 else 0.0

            taxable_fraction = 1.0
            if ira_after_qcd_and_withdrawals > 0.0 and ira_basis > 0.0:
                taxable_fraction = max(0.0, (ira_after_qcd_and_withdrawals - ira_basis) / ira_after_qcd_and_withdrawals)

            gross_room = room_in_24 / taxable_fraction if taxable_fraction > 0.0 else max(0.0, ira_after_qcd_and_withdrawals)
            gross_affordable = max_affordable / taxable_fraction if taxable_fraction > 0.0 else max(0.0, ira_after_qcd_and_withdrawals)

            conversion = min(float(annual_conversion), gross_room, gross_affordable, max(0.0, ira_after_qcd_and_withdrawals))
            conversion = max(0.0, conversion)

            if conversion > 0:
                taxable_conversion_income = conversion
                if ira_basis > 0.0 and ira_after_qcd_and_withdrawals > 0.0:
                    taxable_conversion_income, _, ira_basis = allocate_ira_basis_pro_rata(
                        ira_balance=ira_after_qcd_and_withdrawals,
                        basis_remaining=ira_basis,
                        amount=conversion,
                    )

                ss_taxable_with_conv = taxable_social_security(
                    total_benefits=total_ss,
                    other_income=taxable_ira_withdrawal + taxable_conversion_income,
                    filing_status=filing_status,
                )

                conversion_tax = calculate_tax_federal_ltcg_qd_simple(
                    ordinary_income=float(ss_taxable_with_conv) + float(taxable_ira_withdrawal) + float(taxable_conversion_income),
                    qualified_dividends=float(qualified_dividends),
                    long_term_capital_gains=float(long_term_capital_gains),
                    deduction=float(deduction),
                    tax_year=calendar_year,
                    filing_status=filing_status,
                ) - calculate_tax_federal_ltcg_qd_simple(
                    ordinary_income=float(ss_taxable_no_conv) + float(taxable_ira_withdrawal),
                    qualified_dividends=float(qualified_dividends),
                    long_term_capital_gains=float(long_term_capital_gains),
                    deduction=float(deduction),
                    tax_year=calendar_year,
                    filing_status=filing_status,
                )
                total_conversions += conversion
                total_conversion_tax += conversion_tax

        if bool(inputs.roth_rules.enabled) and conversion > 0:
            roth_ledger.deposit_conversion(amount=conversion, year_index=yr)

        ss_taxable_final = taxable_social_security(
            total_benefits=total_ss,
            other_income=taxable_ira_withdrawal + taxable_conversion_income,
            filing_status=filing_status,
        )
        total_taxable_income = max(
            0.0,
            (ss_taxable_final + taxable_ira_withdrawal + taxable_conversion_income + qualified_dividends + long_term_capital_gains) - float(deduction),
        )
        income_tax = calculate_tax_federal_ltcg_qd_simple(
            ordinary_income=float(ss_taxable_final) + float(taxable_ira_withdrawal) + float(taxable_conversion_income),
            qualified_dividends=float(qualified_dividends),
            long_term_capital_gains=float(long_term_capital_gains),
            deduction=float(deduction),
            tax_year=calendar_year,
            filing_status=filing_status,
        )

        state_tax = 0.0
        if bool(getattr(inputs, "state_tax", None)) and bool(inputs.state_tax.enabled) and float(inputs.state_tax.rate) > 0:
            base = str(getattr(inputs.state_tax, "base", "agi"))
            agi_approx = (
                float(taxable_ira_withdrawal)
                + float(taxable_conversion_income)
                + float(ss_taxable_final)
                + float(qualified_dividends)
                + float(long_term_capital_gains)
                + float(investment_income)
            )
            base_amount = agi_approx if base == "agi" else float(total_taxable_income)
            state_tax = float(inputs.state_tax.rate) * max(0.0, float(base_amount))
            total_state_tax += state_tax

        mr_for_grossup = marginal_rate_ordinary_income(
            taxable_income=total_taxable_income,
            tax_year=calendar_year,
            filing_status=filing_status,
        )

        # IRMAA (Medicare premium surcharges): 2-year lookback MAGI.
        irmaa_cost = 0.0
        medicare_part_b_base_cost = 0.0
        magi_current_year = (
            float(taxable_ira_withdrawal)
            + float(taxable_conversion_income)
            + float(ss_taxable_final)
            + float(qualified_dividends)
            + float(long_term_capital_gains)
            + float(investment_income)
        )
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

        niit_tax = 0.0
        if bool(getattr(inputs, "niit", None)) and bool(inputs.niit.enabled):
            niit_tax = calculate_niit(
                magi=magi_current_year,
                net_investment_income=investment_income,
                filing_status=filing_status,
            )
            total_niit_tax += niit_tax

        if roth_penalty_tax > 0:
            total_roth_penalty_tax += float(roth_penalty_tax)

        rmd_taxable = max(0.0, total_rmd - qcd_from_rmd)
        if taxable_ira_withdrawal > 0:
            rmd_share = rmd_taxable / taxable_ira_withdrawal
            rmd_tax = income_tax * rmd_share
        else:
            rmd_tax = 0.0
        total_rmd_tax += rmd_tax

        # Update balances
        ira -= total_ira_outflow
        ira -= conversion
        roth += conversion
        roth -= from_roth
        taxable -= from_taxable

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

        if roth_penalty_tax > 0:
            taxable, ira = pay_tax(
                taxable=taxable,
                ira=ira,
                tax_due=float(roth_penalty_tax),
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

        ira *= (1.0 + float(inputs.assumptions.ira_return))
        roth *= (1.0 + float(inputs.assumptions.roth_return))
        taxable *= (1.0 + float(inputs.assumptions.taxable_return))

        ira = max(0.0, ira)
        roth = max(0.0, roth)
        taxable = max(0.0, taxable)

        yearly_details.append(
            {
                "year": yr + 1,
                "calendar_year": calendar_year,
                "inflation_multiplier": inflation_multiplier,
                # Generic (stable) keys for downstream exports / agent use
                "spouse1_age": spouse1_age,
                "spouse2_age": spouse2_age,
                # Legacy notebook-derived keys (kept for backwards compatibility)
                "rajesh_age": spouse1_age,
                "terri_age": spouse2_age,
                "ss_income": total_ss,
                "rmd": total_rmd,
                "from_ira": taxable_ira_withdrawal,
                "qcd": qcd,
                "charity_need": charity_need,
                "from_taxable": from_taxable,
                "from_roth": from_roth,
                "conversion": conversion,
                "conversion_tax": conversion_tax,
                "income_tax": income_tax,
                "state_tax": state_tax,
                "irmaa_cost": irmaa_cost,
                "medicare_part_b_base_premium_cost": medicare_part_b_base_cost,
                "niit_tax": niit_tax,
                "roth_penalty_tax": float(roth_penalty_tax),
                "magi": magi_current_year,
                "investment_income": investment_income,
                "ira_end": ira,
                "roth_end": roth,
                "taxable_end": taxable,
            }
        )

        inflation_multiplier *= (1.0 + float(inputs.assumptions.inflation_rate))

    after_tax = ira * 0.75 + roth + taxable * 0.92
    legacy = ira * (1.0 - 0.28) + roth + taxable * 0.95

    heirs_after_tax = 0.0
    if bool(heirs.enabled):
        heirs_years = int(heirs.distribution_years)
        heirs_from_ira = simulate_inherited_distribution_after_tax(
            pretax_balance=ira,
            distribution_years=heirs_years,
            pretax_return=float(inputs.assumptions.ira_return),
            beneficiary_tax_rate=float(heirs.heir_tax_rate),
            beneficiary_taxable_return=float(inputs.assumptions.taxable_return),
        )
        heirs_from_roth = simulate_inherited_roth_after_tax(
            roth_balance=roth,
            distribution_years=heirs_years,
            roth_return=float(inputs.assumptions.roth_return),
            beneficiary_taxable_return=float(inputs.assumptions.taxable_return),
        )
        heirs_after_tax = heirs_from_ira + heirs_from_roth + taxable * 0.95

    end_inflation_multiplier = float(yearly_details[-1].get("inflation_multiplier", 1.0)) if yearly_details else 1.0
    after_tax_today = after_tax / end_inflation_multiplier
    legacy_today = legacy / end_inflation_multiplier
    heirs_after_tax_today = heirs_after_tax / end_inflation_multiplier

    discount_rate = float(inputs.household.discount_rate)
    taxes_today_series = [
        (
            float(row.get("income_tax", 0.0))
            + float(row.get("conversion_tax", 0.0))
            + float(row.get("state_tax", 0.0))
            + float(row.get("irmaa_cost", 0.0))
            + float(row.get("medicare_part_b_base_premium_cost", 0.0))
            + float(row.get("niit_tax", 0.0))
            + float(row.get("roth_penalty_tax", 0.0))
        )
        / float(row.get("inflation_multiplier", 1.0) or 1.0)
        for row in yearly_details
    ]
    npv_taxes_today = npv(taxes_today_series, discount_rate=discount_rate)

    # "First RMD" = first year with a non-zero RMD (including year 1 if already eligible).
    first_rmd = 0.0
    for row in yearly_details:
        rmd_val = float(row.get("rmd", 0.0))
        if rmd_val > 0:
            first_rmd = rmd_val
            break

    return {
        "path_name": path_name,
        "total_conversions": total_conversions,
        "total_conversion_tax": total_conversion_tax,
        "effective_conv_rate": (total_conversion_tax / total_conversions * 100.0) if total_conversions > 0 else 0.0,
        "total_rmds": total_rmds,
        "total_rmd_tax": total_rmd_tax,
        "total_irmaa_cost": total_irmaa_cost,
        "total_medicare_part_b_base_premium_cost": total_medicare_part_b_base_premium_cost,
        "total_niit_tax": total_niit_tax,
        "total_roth_penalty_tax": total_roth_penalty_tax,
        "total_state_tax": total_state_tax,
        "ira": ira,
        "roth": roth,
        "taxable": taxable,
        "after_tax": after_tax,
        "legacy": legacy,
        "after_tax_today": after_tax_today,
        "legacy_today": legacy_today,
        "npv_taxes_today": npv_taxes_today,
        "heirs_after_tax": heirs_after_tax,
        "heirs_after_tax_today": heirs_after_tax_today,
        "first_rmd": first_rmd,
        "yearly_details": yearly_details,
    }
