print("═" * 80)
print("💰 CHAPTER 4: MAXIMIZING YOUR WEALTH")
print("═" * 80)

print(f"""
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WHAT DOES "MAXIMIZE WEALTH" MEAN?                        │
└─────────────────────────────────────────────────────────────────────────────┘

There are TWO ways to think about maximizing wealth:

  1️⃣  MAXIMIZE SPENDABLE INCOME
      → Focus on after-tax dollars YOU can spend
      → Minimize lifetime taxes
      → Prioritize Roth (tax-free withdrawals)

  2️⃣  MAXIMIZE TOTAL ACCOUNT BALANCES  
      → Don't pay taxes until forced (RMDs)
      → Let pre-tax accounts grow tax-deferred
      → May result in higher total, but lower after-tax value

  For MOST retirees, Option 1 is better because:
  • You actually GET to use the money
  • Roth withdrawals don't trigger SS taxation
  • Roth isn't subject to RMDs
  • More flexibility in retirement

┌─────────────────────────────────────────────────────────────────────────────┐
│                    YOUR OPTIMAL STRATEGY FOR WEALTH                         │
└─────────────────────────────────────────────────────────────────────────────┘

  Based on your situation:
  • ${JOINT_TAXABLE_ACCOUNTS:,} in taxable (to pay conversion taxes)
  • ${ANNUAL_INCOME_NEED:,}/year income need
  • 12 years before RMDs

  ✅ RECOMMENDED: PATH B - SMART CONVERSIONS

     Convert ~$500,000 over 4-5 years
     ├── Pay ~$120,000 in conversion taxes (from taxable)
     ├── Move $500,000 to Roth (grows 100% tax-free)
     ├── Reduce first RMD by ~${path_a_first_rmd - path_b_first_rmd:,.0f}
     └── Gain ~${path_b_after_tax - path_a_after_tax:,.0f} in after-tax wealth

  📊 25-YEAR OUTCOME:
     • After-Tax Wealth: ${path_b_after_tax:,.0f}
     • vs Doing Nothing: +${path_b_after_tax - path_a_after_tax:,.0f}
""")