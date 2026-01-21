print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                 📋 HOUSEHOLD RETIREMENT QUICK REFERENCE                       ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  YOUR NUMBERS:                                                                ║
║  ─────────────────────────────────────────────────────────────────────────    ║
""")
print(f"""║  Total Wealth:         ${TOTAL_WEALTH:>12,.0f}                                    ║""")
print(f"""║  Pre-Tax IRAs:         ${TOTAL_PRETAX:>12,.0f}                                    ║""")
print(f"""║  Taxable Account:      ${JOINT_TAXABLE_ACCOUNTS:>12,.0f}                                    ║""")
print(f"""║  Monthly Income Need:  ${MONTHLY_INCOME_NEED:>12,.0f}                                    ║""")
print(f"""║  Cash Reserve:         ${MINIMUM_CASH_RESERVE:>12,.0f}                                    ║""")
print("""
║                                                                               ║
║  CONVERSION TARGETS:                                                          ║
║  ─────────────────────────────────────────────────────────────────────────    ║
║  Years 1-4:  $100,000 - $150,000/year                                         ║
║  Year 5:     $50,000 - $75,000 (Spouse 2 SS starts)                           ║
║  Years 6-7:  $25,000 - $50,000 (if room)                                      ║
║  Year 8+:    Evaluate annually                                                ║
║                                                                               ║
║  STOP SIGNALS:                                                                ║
║  ─────────────────────────────────────────────────────────────────────────    ║
║  🛑 Taxable account < $125,000                                                ║
║  🛑 Conversion would push into 32% bracket                                    ║
║  🛑 RMDs already at acceptable level (<$100K/year)                            ║
║                                                                               ║
║  KEY DATES:                                                                   ║
║  ─────────────────────────────────────────────────────────────────────────    ║""")
print(f"""║  {2025 + years_to_terri_ss}: {SPOUSE2_NAME} SS starts (+${SPOUSE2_SS_ANNUAL:,}/year)                              ║""")
print(f"""║  {2025 + years_to_rajesh_ss}: {SPOUSE1_NAME} SS starts (+${SPOUSE1_SS_ANNUAL:,}/year)                             ║""")
print(f"""║  {2025 + years_to_terri_rmd}: {SPOUSE2_NAME} RMDs begin (age 73)                                      ║""")
print(f"""║  {2025 + years_to_rajesh_rmd}: {SPOUSE1_NAME} RMDs begin (age 73)                                     ║""")
print("""
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
""")