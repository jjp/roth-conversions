# =============================================================================
# SETUP: Import libraries and define ALL shared functions
# =============================================================================
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Optional

# Suppress warnings for cleaner output
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# TAX CALCULATION FUNCTIONS (2024 MFJ Brackets)
# =============================================================================

STANDARD_DEDUCTION_MFJ = 30000  # Approximate 2025 standard deduction

def calculate_tax_mfj(taxable_income):
    """Calculate federal tax for Married Filing Jointly (2024 brackets)"""
    if taxable_income <= 0:
        return 0
    brackets = [
        (23200, 0.10), (94300, 0.12), (201050, 0.22),
        (383900, 0.24), (487450, 0.32), (731200, 0.35), (float('inf'), 0.37)
    ]
    tax = 0
    prev = 0
    for limit, rate in brackets:
        if taxable_income <= prev:
            break
        taxable_in_bracket = min(taxable_income, limit) - prev
        tax += taxable_in_bracket * rate
        prev = limit
    return tax

def get_marginal_rate(taxable_income):
    """Get marginal tax rate for a given taxable income"""
    if taxable_income <= 0:
        return 0.10
    brackets = [
        (23200, 0.10), (94300, 0.12), (201050, 0.22),
        (383900, 0.24), (487450, 0.32), (731200, 0.35), (float('inf'), 0.37)
    ]
    for limit, rate in brackets:
        if taxable_income <= limit:
            return rate
    return 0.37

# =============================================================================
# RMD TABLE (IRS Uniform Lifetime Table)
# =============================================================================

RMD_DIVISORS = {
    72: 27.4, 73: 26.5, 74: 25.5, 75: 24.6, 76: 23.7, 77: 22.9, 78: 22.0,
    79: 21.1, 80: 20.2, 81: 19.4, 82: 18.5, 83: 17.7, 84: 16.8, 85: 16.0,
    86: 15.2, 87: 14.4, 88: 13.7, 89: 12.9, 90: 12.2, 91: 11.5, 92: 10.8,
    93: 10.1, 94: 9.5, 95: 8.9
}

def calculate_rmd(ira_balance, age):
    """Calculate Required Minimum Distribution"""
    if age < 73:
        return 0
    divisor = RMD_DIVISORS.get(age, 8.9)
    return ira_balance / divisor

# =============================================================================
# PROJECTION FUNCTION (used by all analysis cells)
# =============================================================================

def project_with_tax_tracking(
    annual_conversion,
    conversion_years,
    allow_32_bracket=False,
    # These will be set when called from cells that have the data
    total_pretax=None,
    total_roth=None,
    joint_taxable=None,
    spouse1_age=None,
    spouse2_age=None,
    spouse1_ss=None,
    spouse2_ss=None,
    years_to_s1_ss=None,
    years_to_s2_ss=None,
    annual_income=None,
    min_cash=None,
    ira_return=None,
    roth_return=None,
    taxable_return=None,
    inflation=None,
    # Monte Carlo (optional): per-year series. If provided, overrides scalar inputs above.
    horizon_years: int = 25,
    ira_returns=None,
    roth_returns=None,
    taxable_returns=None,
    inflation_rates=None,
    ): 
    """
    Project retirement path with detailed tax tracking.
    
    Parameters:
    -----------
    annual_conversion : float - Target annual conversion amount
    conversion_years : int - How many years to do conversions  
    allow_32_bracket : bool - If True, allow conversions into 32% bracket
    
    Monte Carlo extension (optional):
    - Provide `*_returns` arrays (length >= horizon_years) to simulate year-by-year returns.
    - Provide `inflation_rates` array (length >= horizon_years) to simulate year-by-year inflation.
    """
    
    if horizon_years <= 0:
        raise ValueError("horizon_years must be > 0")

    def _validate_series(name, series):
        if series is None:
            return
        if len(series) < horizon_years:
            raise ValueError(f"{name} must have length >= horizon_years ({horizon_years})")

    _validate_series("ira_returns", ira_returns)
    _validate_series("roth_returns", roth_returns)
    _validate_series("taxable_returns", taxable_returns)
    _validate_series("inflation_rates", inflation_rates)
    
    # Starting balances
    ira = total_pretax
    roth = total_roth
    taxable = joint_taxable
    
    # Tracking
    yearly_data = []
    cumulative_conv_tax = 0
    cumulative_rmd_tax = 0
    cumulative_total_tax = 0
    total_conversions = 0
    total_rmds = 0
    
    inflation_multiplier = 1.0
    
    for yr in range(horizon_years):
        rajesh_age = spouse1_age + yr
        terri_age = spouse2_age + yr
        
        # Use per-year simulated rates if provided
        ira_r = ira_returns[yr] if ira_returns is not None else ira_return
        roth_r = roth_returns[yr] if roth_returns is not None else roth_return
        taxable_r = taxable_returns[yr] if taxable_returns is not None else taxable_return
        infl_r = inflation_rates[yr] if inflation_rates is not None else inflation
        
        # === INCOME SOURCES ===
        ss1 = spouse1_ss if yr >= years_to_s1_ss else 0
        ss2 = spouse2_ss if yr >= years_to_s2_ss else 0
        total_ss = ss1 + ss2
        ss_taxable = total_ss * 0.85
        
        income_need = annual_income * inflation_multiplier
        from_savings_needed = max(0, income_need - total_ss)
        
        # === RMDs ===
        rajesh_rmd = calculate_rmd(ira * 0.33, rajesh_age)
        terri_rmd = calculate_rmd(ira * 0.67, terri_age)
        total_rmd = rajesh_rmd + terri_rmd
        total_rmds += total_rmd
        
        rmd_for_income = min(total_rmd, from_savings_needed)
        remaining_need = from_savings_needed - rmd_for_income
        
        # === WITHDRAWALS ===
        from_taxable = min(remaining_need * 0.5, max(0, taxable - min_cash))
        from_roth = min(remaining_need * 0.3, roth)
        from_ira_extra = max(0, remaining_need - from_taxable - from_roth)
        total_ira_withdrawal = total_rmd + from_ira_extra
        
        # === BASE TAXABLE INCOME (before conversions) ===
        base_taxable_income = ss_taxable + total_ira_withdrawal - STANDARD_DEDUCTION_MFJ
        base_taxable_income = max(0, base_taxable_income)
        
        # === ROTH CONVERSIONS ===
        conversion = 0
        conversion_tax = 0
        conversion_bracket = 0
        
        if yr < conversion_years and annual_conversion > 0:
            available_for_conv_tax = max(0, taxable - min_cash - from_taxable)
            
            # Bracket limits (MFJ 2024)
            bracket_24_ceiling = 383900
            bracket_32_ceiling = 487450
            
            if allow_32_bracket:
                room_in_brackets = max(0, bracket_32_ceiling - base_taxable_income)
            else:
                room_in_brackets = max(0, bracket_24_ceiling - base_taxable_income)
            
            max_affordable = available_for_conv_tax / 0.28 if available_for_conv_tax > 0 else 0
            conversion = min(annual_conversion, room_in_brackets, max_affordable, ira - total_ira_withdrawal)
            conversion = max(0, conversion)
            
            if conversion > 0:
                income_after_conv = base_taxable_income + conversion
                conversion_tax = calculate_tax_mfj(income_after_conv) - calculate_tax_mfj(base_taxable_income)
                
                if base_taxable_income + conversion > bracket_24_ceiling:
                    conversion_bracket = 32
                elif base_taxable_income + conversion > 201050:
                    conversion_bracket = 24
                else:
                    conversion_bracket = 22
                
                total_conversions += conversion
                cumulative_conv_tax += conversion_tax
        
        # === RMD TAX ===
        total_taxable_income = ss_taxable + total_ira_withdrawal - STANDARD_DEDUCTION_MFJ
        total_taxable_income = max(0, total_taxable_income)
        income_tax = calculate_tax_mfj(total_taxable_income)
        
        if total_ira_withdrawal > 0:
            rmd_share = total_rmd / total_ira_withdrawal
            rmd_tax = income_tax * rmd_share
        else:
            rmd_tax = 0
        
        cumulative_rmd_tax += rmd_tax
        cumulative_total_tax = cumulative_conv_tax + cumulative_rmd_tax
        
        # === UPDATE BALANCES ===
        ira -= total_ira_withdrawal
        ira -= conversion
        roth += conversion
        roth -= from_roth
        taxable -= from_taxable
        taxable -= conversion_tax
        taxable -= income_tax * 0.5
        
        ira *= (1 + ira_r)
        roth *= (1 + roth_r)
        taxable *= (1 + taxable_r)
        
        ira = max(0, ira)
        roth = max(0, roth)
        taxable = max(0, taxable)
        
        yearly_data.append({
            'year': yr + 1,
            'calendar_year': 2025 + yr,
            'rajesh_age': rajesh_age,
            'terri_age': terri_age,
            'conversion': conversion,
            'conversion_tax': conversion_tax,
            'conversion_bracket': conversion_bracket,
            'rmd': total_rmd,
            'rmd_tax': rmd_tax,
            'cumulative_conv_tax': cumulative_conv_tax,
            'cumulative_rmd_tax': cumulative_rmd_tax,
            'cumulative_total_tax': cumulative_total_tax,
            'ira': ira,
            'roth': roth,
            'taxable': taxable
        })
        
        # Update inflation multiplier at end of year so year 0 uses today's dollars
        inflation_multiplier *= (1 + infl_r)
    
    after_tax = ira * 0.75 + roth + taxable * 0.92
    legacy = ira * (1 - 0.28) + roth + taxable * 0.95
    
    return {
        'total_conversions': total_conversions,
        'total_conv_tax': cumulative_conv_tax,
        'total_rmds': total_rmds,
        'total_rmd_tax': cumulative_rmd_tax,
        'total_lifetime_tax': cumulative_total_tax,
        'after_tax': after_tax,
        'legacy': legacy,
        'yearly_data': yearly_data
    }

print("✅ Libraries and all shared functions loaded successfully")