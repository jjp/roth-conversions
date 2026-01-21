# =============================================================================
# 📊 CHAPTER 9: THE 32% QUESTION
# =============================================================================
# 
# THE QUESTION: If I convert aggressively and pay 32% tax now, will the 
# savings from lower RMDs later make up for it? And when does that happen?
#
# This requires comparing:
# - Scenario A: Stay in 24% bracket (conservative conversions)
# - Scenario B: Push into 32% bracket (aggressive conversions)
#
# We need to track cumulative tax paid over time and find the crossover point.
# =============================================================================

print("═" * 80)
print("📊 CHAPTER 9: THE 32% QUESTION - IS AGGRESSIVE CONVERTING WORTH IT?")
print("═" * 80)

# =============================================================================
# ENHANCED PROJECTION WITH CUMULATIVE TAX TRACKING
# =============================================================================

def project_with_tax_tracking_ch9(annual_conversion, conversion_years, allow_32_bracket=False):
    """
    Project with detailed tax tracking to find breakeven points.
    
    Parameters:
    -----------
    annual_conversion : float
        Target annual conversion amount
    conversion_years : int
        How many years to do conversions
    allow_32_bracket : bool
        If True, allow conversions that push into 32% bracket
        If False, cap conversions at 24% bracket ceiling
    """
    
    # Starting balances
    ira = TOTAL_PRETAX
    roth = TOTAL_ROTH
    taxable = JOINT_TAXABLE_ACCOUNTS
    
    # Tracking
    yearly_data = []
    cumulative_conv_tax = 0
    cumulative_rmd_tax = 0
    cumulative_total_tax = 0
    total_conversions = 0
    total_rmds = 0
    
    for yr in range(25):
        rajesh_age = SPOUSE1_AGE + yr
        terri_age = SPOUSE2_AGE + yr
        
        # === INCOME SOURCES ===
        ss1 = SPOUSE1_SS_ANNUAL if yr >= years_to_rajesh_ss else 0
        ss2 = SPOUSE2_SS_ANNUAL if yr >= years_to_terri_ss else 0
        total_ss = ss1 + ss2
        ss_taxable = total_ss * 0.85
        
        income_need = ANNUAL_INCOME_NEED * (1 + INFLATION_RATE) ** yr
        from_savings_needed = max(0, income_need - total_ss)
        
        # === RMDs ===
        rajesh_rmd = calculate_rmd(ira * 0.33, rajesh_age)
        terri_rmd = calculate_rmd(ira * 0.67, terri_age)
        total_rmd = rajesh_rmd + terri_rmd
        total_rmds += total_rmd
        
        rmd_for_income = min(total_rmd, from_savings_needed)
        remaining_need = from_savings_needed - rmd_for_income
        
        # === WITHDRAWALS ===
        from_taxable = min(remaining_need * 0.5, max(0, taxable - MINIMUM_CASH_RESERVE))
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
            available_for_conv_tax = max(0, taxable - MINIMUM_CASH_RESERVE - from_taxable)
            
            # Bracket limits (MFJ 2024)
            bracket_24_ceiling = 383900  # Top of 24% bracket
            bracket_32_ceiling = 487450  # Top of 32% bracket
            
            if allow_32_bracket:
                # Allow conversions up to 32% bracket ceiling
                room_in_brackets = max(0, bracket_32_ceiling - base_taxable_income)
            else:
                # Stay within 24% bracket
                room_in_brackets = max(0, bracket_24_ceiling - base_taxable_income)
            
            max_affordable = available_for_conv_tax / 0.28 if available_for_conv_tax > 0 else 0
            conversion = min(annual_conversion, room_in_brackets, max_affordable, ira - total_ira_withdrawal)
            conversion = max(0, conversion)
            
            if conversion > 0:
                income_after_conv = base_taxable_income + conversion
                conversion_tax = calculate_tax_mfj(income_after_conv) - calculate_tax_mfj(base_taxable_income)
                
                # Determine what bracket the conversion hit
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
        
        ira *= (1 + IRA_RETURN)
        roth *= (1 + ROTH_RETURN)
        taxable *= (1 + TAXABLE_RETURN)
        
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

# =============================================================================
# RUN THE SCENARIOS
# =============================================================================

# Scenario 1: Conservative - Stay in 24% bracket ($100K/yr for 5 years)
conservative = project_with_tax_tracking_ch9(100_000, 5, allow_32_bracket=False)

# Scenario 2: Aggressive - Push into 32% bracket ($175K/yr for 8 years)
aggressive = project_with_tax_tracking_ch9(175_000, 8, allow_32_bracket=True)

# Scenario 3: Very Aggressive - Max conversions ($200K/yr for 10 years)
very_aggressive = project_with_tax_tracking_ch9(200_000, 10, allow_32_bracket=True)

# Scenario 4: Do Nothing (baseline)
do_nothing = project_with_tax_tracking_ch9(0, 0, allow_32_bracket=False)

# =============================================================================
# DISPLAY THE ANALYSIS
# =============================================================================

print(f"""
┌─────────────────────────────────────────────────────────────────────────────┐
│                    THE QUESTION YOU'RE REALLY ASKING                        │
└─────────────────────────────────────────────────────────────────────────────┘

  "If I pay 32% tax on conversions NOW, will the reduced RMDs LATER
   save me enough to make it worthwhile? And when does breakeven occur?"

  This is the right question! Let's analyze it.

┌─────────────────────────────────────────────────────────────────────────────┐
│                    THE SCENARIOS                                            │
└─────────────────────────────────────────────────────────────────────────────┘

  📊 SCENARIO COMPARISON:
  
  ┌──────────────────────┬─────────────────┬─────────────────┬─────────────────┐
  │                      │  CONSERVATIVE   │   AGGRESSIVE    │ VERY AGGRESSIVE │
  │                      │  (Stay ≤24%)    │  (Allow 32%)    │   (Max 32%)     │
  ├──────────────────────┼─────────────────┼─────────────────┼─────────────────┤
  │ Conversion Target    │ $100K/yr × 5yr  │ $175K/yr × 8yr  │ $200K/yr × 10yr │
  │ Total Converted      │ ${conservative['total_conversions']:>13,.0f} │ ${aggressive['total_conversions']:>13,.0f} │ ${very_aggressive['total_conversions']:>13,.0f} │
  │ Conversion Tax Paid  │ ${conservative['total_conv_tax']:>13,.0f} │ ${aggressive['total_conv_tax']:>13,.0f} │ ${very_aggressive['total_conv_tax']:>13,.0f} │
  ├──────────────────────┼─────────────────┼─────────────────┼─────────────────┤
  │ Total RMDs (25 yrs)  │ ${conservative['total_rmds']:>13,.0f} │ ${aggressive['total_rmds']:>13,.0f} │ ${very_aggressive['total_rmds']:>13,.0f} │
  │ Total RMD Tax        │ ${conservative['total_rmd_tax']:>13,.0f} │ ${aggressive['total_rmd_tax']:>13,.0f} │ ${very_aggressive['total_rmd_tax']:>13,.0f} │
  ├──────────────────────┼─────────────────┼─────────────────┼─────────────────┤
  │ LIFETIME TAX         │ ${conservative['total_lifetime_tax']:>13,.0f} │ ${aggressive['total_lifetime_tax']:>13,.0f} │ ${very_aggressive['total_lifetime_tax']:>13,.0f} │
  │ vs Conservative      │ ${0:>13,.0f} │ ${aggressive['total_lifetime_tax'] - conservative['total_lifetime_tax']:>+13,.0f} │ ${very_aggressive['total_lifetime_tax'] - conservative['total_lifetime_tax']:>+13,.0f} │
  ├──────────────────────┼─────────────────┼─────────────────┼─────────────────┤
  │ After-Tax Wealth     │ ${conservative['after_tax']:>13,.0f} │ ${aggressive['after_tax']:>13,.0f} │ ${very_aggressive['after_tax']:>13,.0f} │
  │ Legacy to Kids       │ ${conservative['legacy']:>13,.0f} │ ${aggressive['legacy']:>13,.0f} │ ${very_aggressive['legacy']:>13,.0f} │
  └──────────────────────┴─────────────────┴─────────────────┴─────────────────┘
""")

# =============================================================================
# BREAKEVEN ANALYSIS
# =============================================================================

print("""
┌─────────────────────────────────────────────────────────────────────────────┐
│              📈 BREAKEVEN ANALYSIS: WHEN DOES 32% PAY OFF?                  │
└─────────────────────────────────────────────────────────────────────────────┘
""")

# Find the crossover point
print("  Year  Conservative         Aggressive           Difference")
print("        Cumul. Tax           Cumul. Tax           (Neg = Aggressive ahead)")
print("  ────  ───────────────────  ───────────────────  ─────────────────────")

crossover_year = None
for i in range(25):
    cons_data = conservative['yearly_data'][i]
    agg_data = aggressive['yearly_data'][i]
    
    diff = agg_data['cumulative_total_tax'] - cons_data['cumulative_total_tax']
    
    if diff < 0 and crossover_year is None:
        crossover_year = i + 1
        marker = " ← BREAKEVEN!"
    elif diff < 0:
        marker = " ✓"
    else:
        marker = ""
    
    # Show key years
    if i < 10 or i >= 11 or (crossover_year and abs(i + 1 - crossover_year) <= 1):
        print(f"  {i+1:>4}  ${cons_data['cumulative_total_tax']:>17,.0f}  ${agg_data['cumulative_total_tax']:>17,.0f}  ${diff:>+18,.0f}{marker}")

print(f"""
  ═══════════════════════════════════════════════════════════════════════════
""")

# =============================================================================
# THE VERDICT
# =============================================================================

print("""
┌─────────────────────────────────────────────────────────────────────────────┐
│                       🎯 THE VERDICT                                        │
└─────────────────────────────────────────────────────────────────────────────┘
""")

# Determine best strategy
best_wealth = max(conservative['after_tax'], aggressive['after_tax'], very_aggressive['after_tax'])
if best_wealth == very_aggressive['after_tax']:
    best_strategy = "VERY AGGRESSIVE (200K/yr, allow 32%)"
    best = very_aggressive
elif best_wealth == aggressive['after_tax']:
    best_strategy = "AGGRESSIVE (175K/yr, allow 32%)"
    best = aggressive
else:
    best_strategy = "CONSERVATIVE (100K/yr, stay ≤24%)"
    best = conservative

lowest_tax = min(conservative['total_lifetime_tax'], aggressive['total_lifetime_tax'], very_aggressive['total_lifetime_tax'])
if lowest_tax == very_aggressive['total_lifetime_tax']:
    lowest_tax_strategy = "VERY AGGRESSIVE"
elif lowest_tax == aggressive['total_lifetime_tax']:
    lowest_tax_strategy = "AGGRESSIVE"
else:
    lowest_tax_strategy = "CONSERVATIVE"

print(f"""
  📊 WHAT THE NUMBERS SHOW:

  ┌─────────────────────────────────────────────────────────────────────────┐
  │ LOWEST LIFETIME TAX:    {lowest_tax_strategy:>20}                       │
  │ HIGHEST AFTER-TAX WEALTH: {best_strategy:>45} │
  └─────────────────────────────────────────────────────────────────────────┘
""")

if crossover_year:
    print(f"""
  ⏱️  BREAKEVEN TIMELINE:
     
     Aggressive strategy breaks even in YEAR {crossover_year} ({2024 + crossover_year})
     That's when {SPOUSE1_NAME} is {SPOUSE1_AGE + crossover_year - 1} and {SPOUSE2_NAME} is {SPOUSE2_AGE + crossover_year - 1}
     
     After Year {crossover_year}, every additional year FAVORS the aggressive strategy
     because the reduced RMDs keep compounding the savings.
""")
else:
    tax_diff = aggressive['total_lifetime_tax'] - conservative['total_lifetime_tax']
    print(f"""
  ⚠️  BREAKEVEN NOT REACHED IN 25 YEARS
     
     The aggressive strategy pays ${tax_diff:,.0f} MORE in lifetime taxes
     The extra conversion tax is NOT recovered through lower RMDs
     in the 25-year projection window.
""")

wealth_diff = best['after_tax'] - conservative['after_tax']
legacy_diff = best['legacy'] - conservative['legacy']

print(f"""
  💰 WEALTH COMPARISON (Aggressive vs Conservative):
     • After-Tax Wealth: ${aggressive['after_tax'] - conservative['after_tax']:>+15,.0f}
     • Legacy to Kids:   ${aggressive['legacy'] - conservative['legacy']:>+15,.0f}
     • Lifetime Tax:     ${aggressive['total_lifetime_tax'] - conservative['total_lifetime_tax']:>+15,.0f}

  🤔 THE TRADEOFF:
""")

if aggressive['after_tax'] > conservative['after_tax']:
    print(f"""
     ✅ YES, paying 32% NOW is worth it!
     
     Even though you pay higher tax rates upfront, the benefits compound:
     • Lower RMDs = less forced taxable income
     • More in Roth = tax-free growth for decades
     • Better legacy = kids inherit tax-free dollars
     
     The math shows aggressive conversion wins by ${aggressive['after_tax'] - conservative['after_tax']:,.0f}
     in after-tax wealth over 25 years.
""")
else:
    print(f"""
     ❌ NO, staying in 24% is the better choice
     
     The 32% tax rate is too steep a price to pay:
     • The extra tax upfront isn't recovered fast enough
     • Conservative conversion is more efficient
     • You keep more of your money
     
     Conservative wins by ${conservative['after_tax'] - aggressive['after_tax']:,.0f}
     in after-tax wealth over 25 years.
""")

print(f"""
  ════════════════════════════════════════════════════════════════════════════

  🔑 KEY INSIGHT:
  
     The answer depends on YOUR timeline and goals:
     
     • If you expect to live 20+ years past RMD start → Aggressive may win
     • If legacy to kids matters most → Aggressive likely wins (Roth is tax-free)
     • If minimizing lifetime tax is the goal → Check which strategy wins above
     • If you need flexibility/liquidity → Conservative preserves taxable account

  ════════════════════════════════════════════════════════════════════════════
""")