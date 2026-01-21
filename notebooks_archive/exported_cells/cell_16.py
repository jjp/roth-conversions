print("═" * 80)
print("📅 CHAPTER 6: YOUR YEAR-BY-YEAR ACTION PLAN")
print("═" * 80)

print(f"""
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE CONVERSION CALENDAR                             │
└─────────────────────────────────────────────────────────────────────────────┘

  ══════════════════════════════════════════════════════════════════════════
  📅 YEARS 1-4 (2025-2028): THE GOLDEN WINDOW
  ══════════════════════════════════════════════════════════════════════════
  
  Ages: {SPOUSE1_AGE}-{SPOUSE1_AGE+3} / {SPOUSE2_AGE}-{SPOUSE2_AGE+3}
  Social Security: None yet
  Tax Situation: Lowest brackets available
  
  ✅ ACTION: Convert $100,000 - $150,000 per year
  
  WHY: 
  • No SS income filling up your brackets
  • Room to fill 22% and 24% brackets cheaply
  • Taxable account can cover taxes
  • Each dollar converted = 25+ years of tax-free growth
  
  YEAR-BY-YEAR:
  ┌────────┬────────────┬─────────────┬─────────────┬──────────────┐
  │ Year   │ Your Ages  │ Convert     │ Est. Tax    │ Taxable After│
  ├────────┼────────────┼─────────────┼─────────────┼──────────────┤
  │ 2025   │ 60/61      │ $125,000    │ $27,500     │ ~$412,000    │
  │ 2026   │ 61/62      │ $125,000    │ $27,500     │ ~$385,000    │
  │ 2027   │ 62/63      │ $125,000    │ $27,500     │ ~$358,000    │
  │ 2028   │ 63/64      │ $125,000    │ $27,500     │ ~$331,000    │
  └────────┴────────────┴─────────────┴─────────────┴──────────────┘
  SUBTOTAL: $500,000 converted, ~$110,000 in taxes

  ══════════════════════════════════════════════════════════════════════════
  📅 YEAR {years_to_terri_ss + 1} ({2025 + years_to_terri_ss}): {SPOUSE2_NAME.upper()}'S SS STARTS
  ══════════════════════════════════════════════════════════════════════════
  
  Ages: {SPOUSE1_AGE + years_to_terri_ss}/{SPOUSE2_AGE + years_to_terri_ss}
  Social Security: +${SPOUSE2_SS_ANNUAL:,}/year ({SPOUSE2_NAME})
  Tax Situation: Less room in lower brackets
  
  ⚠️ ACTION: Reduce conversions to $50,000 - $75,000
  
  WHY:
  • SS income now fills some of your bracket space
  • Converting too much pushes into higher brackets
  • Still valuable, but be more selective

  ══════════════════════════════════════════════════════════════════════════
  📅 YEARS {years_to_terri_ss + 2}-{years_to_terri_ss + 3} ({2025 + years_to_terri_ss + 1}-{2025 + years_to_terri_ss + 2}): TRANSITION PERIOD
  ══════════════════════════════════════════════════════════════════════════
  
  Ages: {SPOUSE1_AGE + years_to_terri_ss + 1}-{SPOUSE1_AGE + years_to_terri_ss + 2}/{SPOUSE2_AGE + years_to_terri_ss + 1}-{SPOUSE2_AGE + years_to_terri_ss + 2}
  Social Security: ${SPOUSE2_SS_ANNUAL:,}/year ({SPOUSE2_NAME})
  
  ⚠️ ACTION: Convert $25,000 - $50,000 if room in 24% bracket
  
  CHECKPOINT: Is your taxable account above $200,000?
  • YES → Continue modest conversions
  • NO → Pause and preserve flexibility

  ══════════════════════════════════════════════════════════════════════════
  📅 YEAR {max(years_to_rajesh_ss, years_to_terri_ss) + 1}+ ({2025 + max(years_to_rajesh_ss, years_to_terri_ss)}+): BOTH SS ACTIVE
  ══════════════════════════════════════════════════════════════════════════
  
  Ages: {SPOUSE1_AGE + max(years_to_rajesh_ss, years_to_terri_ss)}+/{SPOUSE2_AGE + max(years_to_rajesh_ss, years_to_terri_ss)}+
  Social Security: ${SPOUSE1_SS_ANNUAL + SPOUSE2_SS_ANNUAL:,}/year (both)
  
  🔍 ACTION: Evaluate annually - conversion may be minimal or stop
  
  ANNUAL CHECKLIST:
  □ Is taxable > $125,000?              Yes→ Consider | No→ Stop
  □ Will conversion stay in 24% bracket? Yes→ Convert  | No→ Skip
  □ Are RMDs at acceptable level?        No→ Convert   | Yes→ Optional

  ══════════════════════════════════════════════════════════════════════════
  📅 YEAR {min(years_to_rajesh_rmd, years_to_terri_rmd) + 1}+ ({2025 + min(years_to_rajesh_rmd, years_to_terri_rmd)}+): RMDs BEGIN
  ══════════════════════════════════════════════════════════════════════════
  
  Ages: {SPOUSE1_AGE + min(years_to_rajesh_rmd, years_to_terri_rmd)}/{SPOUSE2_AGE + min(years_to_rajesh_rmd, years_to_terri_rmd)}+
  Status: Required Minimum Distributions begin
  
  🛑 CONVERSION WINDOW CLOSES
  
  • RMDs add to taxable income automatically
  • Less room for conversions without hitting high brackets
  • Focus shifts to managing RMDs efficiently
""")