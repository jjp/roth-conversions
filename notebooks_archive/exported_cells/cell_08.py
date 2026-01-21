# =============================================================================
# 📊 THE KEY QUESTION: Is Paying 32% Now Worth It?
# =============================================================================
# 
# If I convert aggressively and pay 32% tax now, will the savings from 
# lower RMDs later make up for it? And when does breakeven occur?
# =============================================================================

print("═" * 80)
print("📊 THE KEY QUESTION: IS PAYING 32% NOW WORTH IT?")
print("═" * 80)

# Helper function that uses the shared projection function with your data
def run_scenario(annual_conv, years, allow_32=False):
    return project_with_tax_tracking(
        annual_conversion=annual_conv,
        conversion_years=years,
        allow_32_bracket=allow_32,
        total_pretax=TOTAL_PRETAX,
        total_roth=TOTAL_ROTH,
        joint_taxable=JOINT_TAXABLE_ACCOUNTS,
        spouse1_age=SPOUSE1_AGE,
        spouse2_age=SPOUSE2_AGE,
        spouse1_ss=SPOUSE1_SS_ANNUAL,
        spouse2_ss=SPOUSE2_SS_ANNUAL,
        years_to_s1_ss=years_to_rajesh_ss,
        years_to_s2_ss=years_to_terri_ss,
        annual_income=ANNUAL_INCOME_NEED,
        min_cash=MINIMUM_CASH_RESERVE,
        ira_return=IRA_RETURN,
        roth_return=ROTH_RETURN,
        taxable_return=TAXABLE_RETURN,
        inflation=INFLATION_RATE
    )

# Run scenarios
conservative = run_scenario(100_000, 5, allow_32=False)   # Stay ≤24%
aggressive = run_scenario(175_000, 8, allow_32=True)       # Allow 32%
very_aggressive = run_scenario(200_000, 10, allow_32=True) # Max 32%
do_nothing = run_scenario(0, 0)

print(f"""
┌─────────────────────────────────────────────────────────────────────────────┐
│                    THE QUESTION YOU'RE REALLY ASKING                        │
└─────────────────────────────────────────────────────────────────────────────┘

  "If I pay 32% tax on conversions NOW, will the reduced RMDs LATER
   save me enough to make it worthwhile? And when does breakeven occur?"

┌─────────────────────────────────────────────────────────────────────────────┐
│                    SCENARIO COMPARISON                                      │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌──────────────────────┬─────────────────┬─────────────────┬─────────────────┐
  │                      │  CONSERVATIVE   │   AGGRESSIVE    │ VERY AGGRESSIVE │
  │                      │  (Stay ≤24%)    │  (Allow 32%)    │   (Max 32%)     │
  ├──────────────────────┼─────────────────┼─────────────────┼─────────────────┤
  │ Conversion Strategy  │ $100K/yr × 5yr  │ $175K/yr × 8yr  │ $200K/yr × 10yr │
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

# Find breakeven point
print("""
┌─────────────────────────────────────────────────────────────────────────────┐
│              📈 BREAKEVEN ANALYSIS: WHEN DOES 32% PAY OFF?                  │
└─────────────────────────────────────────────────────────────────────────────┘
""")
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
    
    if i < 12 or (crossover_year and abs(i + 1 - crossover_year) <= 2):
        print(f"  {i+1:>4}  ${cons_data['cumulative_total_tax']:>17,.0f}  ${agg_data['cumulative_total_tax']:>17,.0f}  ${diff:>+18,.0f}{marker}")

# The verdict
print(f"""
┌─────────────────────────────────────────────────────────────────────────────┐
│                       🎯 THE ANSWER                                         │
└─────────────────────────────────────────────────────────────────────────────┘
""")

if crossover_year:
    print(f"""
  ✅ YES, paying 32% CAN be worth it!
  
  ⏱️  BREAKEVEN: Year {crossover_year} ({2024 + crossover_year})
     That's when {SPOUSE1_NAME} is {SPOUSE1_AGE + crossover_year - 1} and {SPOUSE2_NAME} is {SPOUSE2_AGE + crossover_year - 1}
     
  After Year {crossover_year}, the aggressive strategy SAVES money every year
  because lower RMDs = less forced taxable income = less tax.
""")
else:
    print(f"""
  ❌ NO, paying 32% does NOT pay off in 25 years
  
  The extra tax paid upfront is NOT recovered through lower RMDs.
  Stick with the conservative (24% max) strategy.
""")

# Final comparison
print(f"""
  💰 25-YEAR OUTCOME COMPARISON:
  
     CONSERVATIVE (stay ≤24%):
     • Lifetime tax:      ${conservative['total_lifetime_tax']:>12,.0f}
     • After-tax wealth:  ${conservative['after_tax']:>12,.0f}
     • Legacy to kids:    ${conservative['legacy']:>12,.0f}
     
     AGGRESSIVE (allow 32%):
     • Lifetime tax:      ${aggressive['total_lifetime_tax']:>12,.0f}  ({aggressive['total_lifetime_tax'] - conservative['total_lifetime_tax']:+,.0f})
     • After-tax wealth:  ${aggressive['after_tax']:>12,.0f}  ({aggressive['after_tax'] - conservative['after_tax']:+,.0f})
     • Legacy to kids:    ${aggressive['legacy']:>12,.0f}  ({aggressive['legacy'] - conservative['legacy']:+,.0f})

  🎯 RECOMMENDATION:
""")

if aggressive['after_tax'] > conservative['after_tax']:
    print(f"""     → AGGRESSIVE conversion is BETTER by ${aggressive['after_tax'] - conservative['after_tax']:,.0f}
     → The 32% tax is worth paying because RMD savings compound over time
     → Your kids also inherit ${aggressive['legacy'] - conservative['legacy']:,.0f} more (tax-free Roth)
""")
else:
    print(f"""     → CONSERVATIVE conversion is BETTER by ${conservative['after_tax'] - aggressive['after_tax']:,.0f}
     → The 32% tax is TOO expensive - stick with ≤24% conversions
     → Fill the 24% bracket fully, but don't spill into 32%
""")