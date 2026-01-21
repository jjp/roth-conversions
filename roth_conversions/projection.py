from __future__ import annotations

from typing import Optional, Sequence

from .models import HouseholdInputs, ProjectionResult, ProjectionYear, Strategy, as_float_seq, clamp_series
from .rmd import required_minimum_distribution
from .social_security import taxable_social_security
from .tax import calculate_tax_ordinary_income, marginal_rate_ordinary_income
from .tax_tables import get_bracket_ceiling, get_standard_deduction
from .irmaa_tables import get_irmaa_addons_monthly


STANDARD_DEDUCTION_MFJ_APPROX_2025 = 30_000.0


def _gross_up_for_withholding(net_tax: float, marginal_rate: float) -> float:
    # Approximation: treat IRA withholding as a pre-tax distribution that is withheld.
    # If marginal_rate is 24%, then withholding $24 requires a $100 distribution.
    if net_tax <= 0:
        return 0.0
    r = max(0.0, min(float(marginal_rate), 0.99))
    if r <= 0.0:
        return float(net_tax)
    return float(net_tax) / (1.0 - r)


def _pay_tax(
    *,
    taxable: float,
    ira: float,
    tax_due: float,
    source: str,
    minimum_cash_reserve: float,
    marginal_rate: float,
) -> tuple[float, float]:
    if tax_due <= 0:
        return taxable, ira

    if source == "taxable":
        available_cash = max(0.0, float(taxable) - float(minimum_cash_reserve))
        from_taxable = min(float(tax_due), available_cash)
        taxable -= from_taxable
        remaining = float(tax_due) - from_taxable
        if remaining > 0:
            ira -= _gross_up_for_withholding(remaining, marginal_rate)
        return taxable, ira

    if source == "ira":
        ira -= _gross_up_for_withholding(float(tax_due), marginal_rate)
        return taxable, ira

    raise ValueError(f"unsupported tax payment source: {source!r}")


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

    filing_status = str(inputs.household.tax_filing_status)
    tax_policy = inputs.tax_payment_policy

    cumulative_conv_tax = 0.0
    cumulative_rmd_tax = 0.0
    cumulative_irmaa_cost = 0.0
    total_conversions = 0.0
    total_rmds = 0.0

    inflation_multiplier = 1.0
    yearly: list[ProjectionYear] = []

    magi_by_calendar_year: dict[int, float] = {}

    for yr in range(horizon_years):
        spouse1_age = int(inputs.spouse1.age) + yr
        spouse2_age = int(inputs.spouse2.age) + yr
        calendar_year = int(inputs.household.start_year) + yr

        # Use pinned tax table data when available; fall back to the historical constant only
        # if the filing status isn't supported by the pinned tables.
        try:
            standard_deduction = get_standard_deduction(tax_year=calendar_year, filing_status=filing_status)
        except Exception:
            # Backwards compatibility: old behavior assumed MFJ.
            standard_deduction = float(standard_deduction_mfj)

        ira_r = float(ira_returns[yr]) if ira_returns is not None else float(inputs.assumptions.ira_return)
        roth_r = float(roth_returns[yr]) if roth_returns is not None else float(inputs.assumptions.roth_return)
        taxable_r = float(taxable_returns[yr]) if taxable_returns is not None else float(inputs.assumptions.taxable_return)
        infl_r = float(inflation_rates[yr]) if inflation_rates is not None else float(inputs.assumptions.inflation_rate)

        # Social security
        ss1 = float(inputs.spouse1.ss_annual) if yr >= inputs.years_to_spouse1_ss else 0.0
        ss2 = float(inputs.spouse2.ss_annual) if yr >= inputs.years_to_spouse2_ss else 0.0
        total_ss = ss1 + ss2

        # IRMAA uses (typically) 2-year lookback MAGI; we approximate MAGI as AGI
        # from this model (IRA withdrawals + conversions + taxable SS).
        # We'll compute MAGI after we compute taxable SS for the final income picture.
        irmaa_cost = 0.0

        income_need = float(inputs.plan.annual_income_need) * inflation_multiplier
        from_savings_needed = max(0.0, income_need - total_ss)

        # RMDs (notebook splits IRA 33/67)
        spouse1_rmd = required_minimum_distribution(ira * 0.33, spouse1_age)
        spouse2_rmd = required_minimum_distribution(ira * 0.67, spouse2_age)
        total_rmd = spouse1_rmd + spouse2_rmd
        total_rmds += total_rmd

        rmd_for_income = min(total_rmd, from_savings_needed)
        remaining_need = from_savings_needed - rmd_for_income

        # Withdrawals
        from_taxable = min(remaining_need * 0.5, max(0.0, taxable - float(inputs.plan.minimum_cash_reserve)))
        from_roth = min(remaining_need * 0.3, roth)
        from_ira_extra = max(0.0, remaining_need - from_taxable - from_roth)
        total_ira_withdrawal = total_rmd + from_ira_extra

        # Compute SS taxable using IRS provisional income rules.
        # Note: taxable SS depends on other income (IRA withdrawals, conversions), so we
        # compute "without conversion" and "with conversion" versions when needed.
        ss_taxable_no_conv = taxable_social_security(
            total_benefits=total_ss,
            other_income=total_ira_withdrawal,
            filing_status=filing_status,
        )
        base_taxable_income = max(0.0, ss_taxable_no_conv + total_ira_withdrawal - float(standard_deduction))

        # Conversions
        conversion = 0.0
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
                (bracket_32_ceiling if strategy.allow_32_bracket else bracket_24_ceiling) - base_taxable_income,
            )

            # Notebook used 0.28 here for max_affordable
            max_affordable = (available_for_conv_tax / 0.28) if available_for_conv_tax > 0 else 0.0
            conversion = min(float(strategy.annual_conversion), room_in_brackets, max_affordable, max(0.0, ira - total_ira_withdrawal))
            conversion = max(0.0, conversion)

            if conversion > 0:
                ss_taxable_with_conv = taxable_social_security(
                    total_benefits=total_ss,
                    other_income=total_ira_withdrawal + conversion,
                    filing_status=filing_status,
                )
                taxable_income_with_conv = max(0.0, ss_taxable_with_conv + total_ira_withdrawal + conversion - float(standard_deduction))
                taxable_income_no_conv = max(0.0, ss_taxable_no_conv + total_ira_withdrawal - float(standard_deduction))

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
                cumulative_conv_tax += conversion_tax

        # Income tax & allocate portion to RMD
        # Income tax after conversion decision.
        ss_taxable_final = taxable_social_security(
            total_benefits=total_ss,
            other_income=total_ira_withdrawal + conversion,
            filing_status=filing_status,
        )
        total_taxable_income = max(0.0, ss_taxable_final + total_ira_withdrawal + conversion - float(standard_deduction))
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

        # Persist MAGI estimate for lookback calculations.
        magi_current_year = float(total_ira_withdrawal) + float(conversion) + float(ss_taxable_final)
        magi_by_calendar_year[calendar_year] = magi_current_year

        if bool(inputs.medicare.irmaa_enabled):
            lookback_year = calendar_year - 2
            lookback_magi = float(magi_by_calendar_year.get(lookback_year, magi_current_year))
            part_b_add, part_d_add = get_irmaa_addons_monthly(
                premium_year=calendar_year,
                filing_status=filing_status,
                magi=lookback_magi,
            )
            covered_people = 2 if filing_status == "MFJ" else 1
            irmaa_cost = (part_b_add + part_d_add) * 12.0 * float(covered_people)
            cumulative_irmaa_cost += irmaa_cost

        if total_ira_withdrawal > 0:
            rmd_share = total_rmd / total_ira_withdrawal
            rmd_tax = income_tax * rmd_share
        else:
            rmd_tax = 0.0

        cumulative_rmd_tax += rmd_tax
        cumulative_total_tax = cumulative_conv_tax + cumulative_rmd_tax

        # Update balances
        ira -= total_ira_withdrawal
        ira -= conversion
        roth += conversion
        roth -= from_roth
        taxable -= from_taxable

        taxable, ira = _pay_tax(
            taxable=taxable,
            ira=ira,
            tax_due=conversion_tax,
            source=str(tax_policy.conversion_tax_payment_source),
            minimum_cash_reserve=float(inputs.plan.minimum_cash_reserve),
            marginal_rate=mr_for_grossup,
        )
        taxable, ira = _pay_tax(
            taxable=taxable,
            ira=ira,
            tax_due=income_tax,
            source=str(tax_policy.income_tax_payment_source),
            minimum_cash_reserve=float(inputs.plan.minimum_cash_reserve),
            marginal_rate=mr_for_grossup,
        )

        # Treat IRMAA as an annual expense paid from taxable (then IRA spillover).
        if irmaa_cost > 0:
            taxable, ira = _pay_tax(
                taxable=taxable,
                ira=ira,
                tax_due=irmaa_cost,
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
                ira_withdrawal=total_ira_withdrawal,
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
            )
        )

        inflation_multiplier *= (1.0 + infl_r)

    after_tax = ira * 0.75 + roth + taxable * 0.92
    legacy = ira * (1.0 - 0.28) + roth + taxable * 0.95

    return ProjectionResult(
        strategy=strategy,
        total_conversions=total_conversions,
        total_conv_tax=cumulative_conv_tax,
        total_rmds=total_rmds,
        total_rmd_tax=cumulative_rmd_tax,
        total_lifetime_tax=cumulative_conv_tax + cumulative_rmd_tax,
        after_tax=after_tax,
        legacy=legacy,
        yearly=tuple(yearly),
        total_irmaa_cost=cumulative_irmaa_cost,
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

    filing_status = str(inputs.household.tax_filing_status)
    tax_policy = inputs.tax_payment_policy

    total_conversions = 0.0
    total_conversion_tax = 0.0
    total_rmds = 0.0
    total_rmd_tax = 0.0
    total_irmaa_cost = 0.0

    yearly_details: list[dict] = []

    magi_by_calendar_year: dict[int, float] = {}

    for yr in range(horizon_years):
        spouse1_age = int(inputs.spouse1.age) + yr
        spouse2_age = int(inputs.spouse2.age) + yr
        calendar_year = int(inputs.household.start_year) + yr

        try:
            standard_deduction = get_standard_deduction(tax_year=calendar_year, filing_status=filing_status)
        except Exception:
            standard_deduction = float(standard_deduction_mfj)

        ss1 = float(inputs.spouse1.ss_annual) if yr >= inputs.years_to_spouse1_ss else 0.0
        ss2 = float(inputs.spouse2.ss_annual) if yr >= inputs.years_to_spouse2_ss else 0.0
        total_ss = ss1 + ss2

        income_need = float(inputs.plan.annual_income_need) * (1.0 + float(inputs.assumptions.inflation_rate)) ** yr
        from_savings_needed = max(0.0, income_need - total_ss)

        spouse1_rmd = required_minimum_distribution(ira * 0.33, spouse1_age)
        spouse2_rmd = required_minimum_distribution(ira * 0.67, spouse2_age)
        total_rmd = spouse1_rmd + spouse2_rmd
        total_rmds += total_rmd

        rmd_for_income = min(total_rmd, from_savings_needed)
        remaining_need = from_savings_needed - rmd_for_income

        from_taxable = min(remaining_need * 0.5, max(0.0, taxable - float(inputs.plan.minimum_cash_reserve)))
        from_roth = min(remaining_need * 0.3, roth)
        from_ira_extra = max(0.0, remaining_need - from_taxable - from_roth)
        total_ira_withdrawal = total_rmd + from_ira_extra

        ss_taxable_no_conv = taxable_social_security(
            total_benefits=total_ss,
            other_income=total_ira_withdrawal,
            filing_status=filing_status,
        )

        conversion = 0.0
        conversion_tax = 0.0
        if yr < int(conversion_years) and float(annual_conversion) > 0:
            available_for_conv_tax = max(0.0, taxable - float(inputs.plan.minimum_cash_reserve) - from_taxable)

            base_taxable_income = max(0.0, ss_taxable_no_conv + total_ira_withdrawal - float(standard_deduction))
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

            conversion = min(float(annual_conversion), room_in_24, max_affordable, max(0.0, ira - total_ira_withdrawal))
            conversion = max(0.0, conversion)

            if conversion > 0:
                ss_taxable_with_conv = taxable_social_security(
                    total_benefits=total_ss,
                    other_income=total_ira_withdrawal + conversion,
                    filing_status=filing_status,
                )

                taxable_income_with_conv = max(0.0, ss_taxable_with_conv + total_ira_withdrawal + conversion - float(standard_deduction))
                taxable_income_no_conv = max(0.0, ss_taxable_no_conv + total_ira_withdrawal - float(standard_deduction))

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
                total_conversion_tax += conversion_tax

        ss_taxable_final = taxable_social_security(
            total_benefits=total_ss,
            other_income=total_ira_withdrawal + conversion,
            filing_status=filing_status,
        )
        total_taxable_income = max(0.0, ss_taxable_final + total_ira_withdrawal + conversion - float(standard_deduction))
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

        # IRMAA (Medicare premium surcharges): 2-year lookback MAGI.
        irmaa_cost = 0.0
        magi_current_year = float(total_ira_withdrawal) + float(conversion) + float(ss_taxable_final)
        magi_by_calendar_year[calendar_year] = magi_current_year
        if bool(inputs.medicare.irmaa_enabled):
            lookback_magi = float(magi_by_calendar_year.get(calendar_year - 2, magi_current_year))
            part_b_add, part_d_add = get_irmaa_addons_monthly(
                premium_year=calendar_year,
                filing_status=filing_status,
                magi=lookback_magi,
            )
            covered_people = 2 if filing_status == "MFJ" else 1
            irmaa_cost = (part_b_add + part_d_add) * 12.0 * float(covered_people)
            total_irmaa_cost += irmaa_cost

        if total_ira_withdrawal > 0:
            rmd_share = total_rmd / total_ira_withdrawal
            rmd_tax = income_tax * rmd_share
        else:
            rmd_tax = 0.0
        total_rmd_tax += rmd_tax

        # Update balances
        ira -= total_ira_withdrawal
        ira -= conversion
        roth += conversion
        roth -= from_roth
        taxable -= from_taxable

        taxable, ira = _pay_tax(
            taxable=taxable,
            ira=ira,
            tax_due=conversion_tax,
            source=str(tax_policy.conversion_tax_payment_source),
            minimum_cash_reserve=float(inputs.plan.minimum_cash_reserve),
            marginal_rate=mr_for_grossup,
        )
        taxable, ira = _pay_tax(
            taxable=taxable,
            ira=ira,
            tax_due=income_tax,
            source=str(tax_policy.income_tax_payment_source),
            minimum_cash_reserve=float(inputs.plan.minimum_cash_reserve),
            marginal_rate=mr_for_grossup,
        )

        if irmaa_cost > 0:
            taxable, ira = _pay_tax(
                taxable=taxable,
                ira=ira,
                tax_due=irmaa_cost,
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
                "rajesh_age": spouse1_age,
                "terri_age": spouse2_age,
                "ss_income": total_ss,
                "rmd": total_rmd,
                "from_ira": total_ira_withdrawal,
                "from_taxable": from_taxable,
                "from_roth": from_roth,
                "conversion": conversion,
                "conversion_tax": conversion_tax,
                "income_tax": income_tax,
                "irmaa_cost": irmaa_cost,
                "ira_end": ira,
                "roth_end": roth,
                "taxable_end": taxable,
            }
        )

    after_tax = ira * 0.75 + roth + taxable * 0.92
    legacy = ira * (1.0 - 0.28) + roth + taxable * 0.95

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
        "ira": ira,
        "roth": roth,
        "taxable": taxable,
        "after_tax": after_tax,
        "legacy": legacy,
        "first_rmd": first_rmd,
        "yearly_details": yearly_details,
    }
