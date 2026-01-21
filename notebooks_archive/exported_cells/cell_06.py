print("═" * 80)
print("💵 CHAPTER 2: YOUR INCOME NEEDS & TIMELINE")
print("═" * 80)

# Key milestones
years_to_terri_ss = SPOUSE2_SS_START_AGE - SPOUSE2_AGE
years_to_rajesh_ss = SPOUSE1_SS_START_AGE - SPOUSE1_AGE
years_to_terri_rmd = 73 - SPOUSE2_AGE
years_to_rajesh_rmd = 73 - SPOUSE1_AGE

print(f"""
┌─────────────────────────────────────────────────────────────────────────────┐
│                         YOUR INCOME REQUIREMENTS                            │
└─────────────────────────────────────────────────────────────────────────────┘

  📋 MONTHLY NEED:    ${MONTHLY_INCOME_NEED:>8,.0f}
  📋 ANNUAL NEED:     ${ANNUAL_INCOME_NEED:>8,.0f}
  📋 CASH RESERVE:    ${MINIMUM_CASH_RESERVE:>8,.0f} (emergency fund)

┌─────────────────────────────────────────────────────────────────────────────┐
│                         YOUR RETIREMENT TIMELINE                            │
└─────────────────────────────────────────────────────────────────────────────┘

  📅 TODAY (2025)
     {SPOUSE1_NAME} is {SPOUSE1_AGE}, {SPOUSE2_NAME} is {SPOUSE2_AGE}
     All income comes from savings (${ANNUAL_INCOME_NEED:,}/year)

  📅 YEAR {years_to_terri_ss} ({2025 + years_to_terri_ss}): {SPOUSE2_NAME}'s Social Security Starts
     └── +${SPOUSE2_SS_ANNUAL:,}/year

  📅 YEAR {years_to_rajesh_ss} ({2025 + years_to_rajesh_ss}): {SPOUSE1_NAME}'s Social Security Starts
     └── +${SPOUSE1_SS_ANNUAL:,}/year
     └── Combined SS: ${SPOUSE1_SS_ANNUAL + SPOUSE2_SS_ANNUAL:,}/year

  📅 YEAR {years_to_terri_rmd} ({2025 + years_to_terri_rmd}): {SPOUSE2_NAME} Turns 73 - RMDs BEGIN!
     └── IRS forces you to withdraw from IRAs
     └── All withdrawals taxed as ordinary income

  📅 YEAR {years_to_rajesh_rmd} ({2025 + years_to_rajesh_rmd}): {SPOUSE1_NAME} Turns 73 - More RMDs

  ⚠️  THE WINDOW: You have {years_to_terri_rmd} years before forced RMDs begin.
     These years are your OPPORTUNITY to convert to Roth strategically!
""")