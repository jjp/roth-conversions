print("═" * 80)
print("👨‍👩‍👧‍👦 CHAPTER 5: MAXIMIZING LEGACY FOR YOUR KIDS")
print("═" * 80)

# Calculate inheritance scenarios
# Assume you live to age 85 (25 years), kids inherit the rest

# What kids receive (after-tax value to THEM)
# IRA: Kids must withdraw within 10 years, taxed at THEIR rate (~25-32%)
# Roth: Kids withdraw tax-free within 10 years
# Taxable: Gets stepped-up basis, minimal tax

kids_tax_rate = 0.28  # Assume kids are in 28% marginal bracket

# PATH A inheritance
path_a_kids_ira = path_a_ira * (1 - kids_tax_rate)  # Kids pay tax
path_a_kids_roth = path_a_roth  # Tax-free to kids
path_a_kids_taxable = path_a_taxable * 0.95  # Stepped-up basis, minimal tax
path_a_kids_total = path_a_kids_ira + path_a_kids_roth + path_a_kids_taxable

# PATH B inheritance
path_b_kids_ira = path_b_ira * (1 - kids_tax_rate)
path_b_kids_roth = path_b_roth  # Tax-free!
path_b_kids_taxable = path_b_taxable * 0.95
path_b_kids_total = path_b_kids_ira + path_b_kids_roth + path_b_kids_taxable

# PATH C inheritance
path_c_kids_ira = path_c_ira * (1 - kids_tax_rate)
path_c_kids_roth = path_c_roth  # Tax-free!
path_c_kids_taxable = path_c_taxable * 0.95
path_c_kids_total = path_c_kids_ira + path_c_kids_roth + path_c_kids_taxable

print(f"""
┌─────────────────────────────────────────────────────────────────────────────┐
│                    THE INHERITANCE TAX PROBLEM                              │
└─────────────────────────────────────────────────────────────────────────────┘

  When your kids inherit your accounts, here's what happens:

  📜 INHERITED IRA (Traditional/SEP):
     • Kids MUST withdraw everything within 10 years (SECURE Act)
     • Every dollar is taxed as THEIR ordinary income
     • If they're working, this could push them into 32-37% brackets!
     • Result: Uncle Sam takes 25-35% of their inheritance

  📜 INHERITED ROTH IRA:
     • Kids MUST withdraw within 10 years
     • BUT... every dollar is 100% TAX-FREE!
     • No impact on their tax bracket
     • Result: Kids keep 100% of the inheritance

  📜 INHERITED TAXABLE ACCOUNT:
     • Gets "stepped-up" cost basis to current value
     • Kids only pay tax on gains AFTER inheritance
     • Result: Very tax-efficient transfer

  💡 KEY INSIGHT: Converting IRA → Roth means YOU pay the tax at 22-24%
     instead of your KIDS paying at 28-35%!

┌─────────────────────────────────────────────────────────────────────────────┐
│                    WHAT YOUR KIDS ACTUALLY RECEIVE                          │
└─────────────────────────────────────────────────────────────────────────────┘

  Assuming you both live to ~85, and kids are in 28% tax bracket:

╔═══════════════════════╦═══════════════════╦═══════════════════╦═══════════════════╗
║                       ║   PATH A:         ║   PATH B:         ║   PATH C:         ║
║   INHERITANCE         ║   Do Nothing      ║   Smart Convert   ║   Aggressive      ║
╠═══════════════════════╬═══════════════════╬═══════════════════╬═══════════════════╣
║ IRA (after kids' tax) ║ ${path_a_kids_ira:>14,.0f}  ║ ${path_b_kids_ira:>14,.0f}  ║ ${path_c_kids_ira:>14,.0f}  ║
║ Roth (100% tax-free)  ║ ${path_a_kids_roth:>14,.0f}  ║ ${path_b_kids_roth:>14,.0f}  ║ ${path_c_kids_roth:>14,.0f}  ║
║ Taxable (stepped-up)  ║ ${path_a_kids_taxable:>14,.0f}  ║ ${path_b_kids_taxable:>14,.0f}  ║ ${path_c_kids_taxable:>14,.0f}  ║
╠═══════════════════════╬═══════════════════╬═══════════════════╬═══════════════════╣
║ KIDS' AFTER-TAX TOTAL ║ ${path_a_kids_total:>14,.0f}  ║ ${path_b_kids_total:>14,.0f}  ║ ${path_c_kids_total:>14,.0f}  ║
║ vs Do Nothing         ║ ${0:>14,.0f}  ║ ${path_b_kids_total - path_a_kids_total:>+14,.0f}  ║ ${path_c_kids_total - path_a_kids_total:>+14,.0f}  ║
╚═══════════════════════╩═══════════════════╩═══════════════════╩═══════════════════╝

  🎯 TO MAXIMIZE LEGACY:
""")

best_for_kids = max(path_a_kids_total, path_b_kids_total, path_c_kids_total)
if best_for_kids == path_c_kids_total:
    best_path = "PATH C (Aggressive)"
    best_amount = path_c_kids_total
    extra = path_c_kids_total - path_a_kids_total
elif best_for_kids == path_b_kids_total:
    best_path = "PATH B (Smart)"
    best_amount = path_b_kids_total
    extra = path_b_kids_total - path_a_kids_total
else:
    best_path = "PATH A (Do Nothing)"
    best_amount = path_a_kids_total
    extra = 0

print(f"""     
     ✅ {best_path} leaves your kids ${best_amount:,.0f}
     ✅ That's ${extra:,.0f} MORE than doing nothing!
     
     The more you convert to Roth NOW:
     • The less tax burden your KIDS face
     • The more flexibility they have
     • The more they actually KEEP
""")