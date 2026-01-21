from __future__ import annotations

from typing import Optional, Sequence

from .models import HouseholdInputs, ProjectionResult, ProjectionYear, Strategy, as_float_seq, clamp_series
from .rmd import required_minimum_distribution
from .tax import calculate_tax_mfj_2024, marginal_rate_mfj_2024


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

    cumulative_conv_tax = 0.0
    cumulative_rmd_tax = 0.0
    total_conversions = 0.0
    total_rmds = 0.0

    inflation_multiplier = 1.0
    yearly: list[ProjectionYear] = []

    for yr in range(horizon_years):
        spouse1_age = int(inputs.spouse1.age) + yr
        spouse2_age = int(inputs.spouse2.age) + yr
        calendar_year = int(inputs.household.start_year) + yr

        ira_r = float(ira_returns[yr]) if ira_returns is not None else float(inputs.assumptions.ira_return)
        roth_r = float(roth_returns[yr]) if roth_returns is not None else float(inputs.assumptions.roth_return)
        taxable_r = float(taxable_returns[yr]) if taxable_returns is not None else float(inputs.assumptions.taxable_return)
        infl_r = float(inflation_rates[yr]) if inflation_rates is not None else float(inputs.assumptions.inflation_rate)

        # Social security
        ss1 = float(inputs.spouse1.ss_annual) if yr >= inputs.years_to_spouse1_ss else 0.0
        ss2 = float(inputs.spouse2.ss_annual) if yr >= inputs.years_to_spouse2_ss else 0.0
        total_ss = ss1 + ss2
        ss_taxable = total_ss * 0.85

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

        base_taxable_income = max(0.0, ss_taxable + total_ira_withdrawal - float(standard_deduction_mfj))

        # Conversions
        conversion = 0.0
        conversion_tax = 0.0
        if yr < int(strategy.conversion_years) and float(strategy.annual_conversion) > 0:
            available_for_conv_tax = max(0.0, taxable - float(inputs.plan.minimum_cash_reserve) - from_taxable)

            bracket_24_ceiling = 383_900.0
            bracket_32_ceiling = 487_450.0
            room_in_brackets = max(0.0, (bracket_32_ceiling if strategy.allow_32_bracket else bracket_24_ceiling) - base_taxable_income)

            # Notebook used 0.28 here for max_affordable
            max_affordable = (available_for_conv_tax / 0.28) if available_for_conv_tax > 0 else 0.0
            conversion = min(float(strategy.annual_conversion), room_in_brackets, max_affordable, max(0.0, ira - total_ira_withdrawal))
            conversion = max(0.0, conversion)

            if conversion > 0:
                income_after_conv = base_taxable_income + conversion
                conversion_tax = calculate_tax_mfj_2024(income_after_conv) - calculate_tax_mfj_2024(base_taxable_income)
                total_conversions += conversion
                cumulative_conv_tax += conversion_tax

        # Income tax & allocate portion to RMD
        total_taxable_income = max(0.0, ss_taxable + total_ira_withdrawal - float(standard_deduction_mfj))
        income_tax = calculate_tax_mfj_2024(total_taxable_income)

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
        taxable -= conversion_tax
        taxable -= income_tax * 0.5  # notebook approximation

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

    total_conversions = 0.0
    total_conversion_tax = 0.0
    total_rmds = 0.0
    total_rmd_tax = 0.0

    yearly_details: list[dict] = []

    for yr in range(horizon_years):
        spouse1_age = int(inputs.spouse1.age) + yr
        spouse2_age = int(inputs.spouse2.age) + yr
        calendar_year = int(inputs.household.start_year) + yr

        ss1 = float(inputs.spouse1.ss_annual) if yr >= inputs.years_to_spouse1_ss else 0.0
        ss2 = float(inputs.spouse2.ss_annual) if yr >= inputs.years_to_spouse2_ss else 0.0
        total_ss = ss1 + ss2
        ss_taxable = total_ss * 0.85

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

        conversion = 0.0
        conversion_tax = 0.0
        if yr < int(conversion_years) and float(annual_conversion) > 0:
            available_for_conv_tax = max(0.0, taxable - float(inputs.plan.minimum_cash_reserve) - from_taxable)

            base_taxable_income = max(0.0, ss_taxable + total_ira_withdrawal - float(standard_deduction_mfj))
            mr = marginal_rate_mfj_2024(base_taxable_income)
            room_in_24 = max(0.0, 383_900.0 - base_taxable_income)
            max_affordable = available_for_conv_tax / mr if mr > 0 else 0.0

            conversion = min(float(annual_conversion), room_in_24, max_affordable, max(0.0, ira - total_ira_withdrawal))
            conversion = max(0.0, conversion)

            if conversion > 0:
                conversion_tax = calculate_tax_mfj_2024(base_taxable_income + conversion) - calculate_tax_mfj_2024(base_taxable_income)
                total_conversions += conversion
                total_conversion_tax += conversion_tax

        total_taxable_income = max(0.0, ss_taxable + total_ira_withdrawal - float(standard_deduction_mfj))
        income_tax = calculate_tax_mfj_2024(total_taxable_income)

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
        taxable -= conversion_tax
        taxable -= income_tax * 0.5

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
        "ira": ira,
        "roth": roth,
        "taxable": taxable,
        "after_tax": after_tax,
        "legacy": legacy,
        "first_rmd": first_rmd,
        "yearly_details": yearly_details,
    }
