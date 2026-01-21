print("═" * 80)
print("🎯 CHAPTER 7: THE BOTTOM LINE")
print("═" * 80)

print(f"""
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SUMMARY: WHAT YOU SHOULD DO                         │
└─────────────────────────────────────────────────────────────────────────────┘

  ╔═══════════════════════════════════════════════════════════════════════════╗
  ║                     YOUR OPTIMAL STRATEGY                                 ║
  ╠═══════════════════════════════════════════════════════════════════════════╣
  ║                                                                           ║
  ║   Convert ~$500,000 to Roth over 4-5 years (2025-2029)                   ║
  ║                                                                           ║
  ║   • Annual conversion: ~$100,000 - $125,000                              ║
  ║   • Conversion taxes: ~$110,000 - $130,000 total                         ║
  ║   • Pay taxes from: Taxable account                                       ║
  ║                                                                           ║
  ╚═══════════════════════════════════════════════════════════════════════════╝

  📊 WHAT THIS ACHIEVES:

     ┌───────────────────────────────────┬──────────────────┐
     │ Metric                            │ Your Outcome     │
     ├───────────────────────────────────┼──────────────────┤
     │ After-tax wealth gain (25 yrs)    │ +${path_b_after_tax - path_a_after_tax:>13,.0f} │
     │ First RMD reduction               │ -${path_a_first_rmd - path_b_first_rmd:>13,.0f} │
     │ Kids' inheritance increase        │ +${path_b_kids_total - path_a_kids_total:>13,.0f} │
     └───────────────────────────────────┴──────────────────┘

  ✅ FOR MAXIMIZING YOUR WEALTH:
     → Convert steadily in Years 1-4 while in low brackets
     → Reduces lifetime taxes by paying 22-24% now vs 28-32% later
     → More tax-free income in retirement
     → More control (Roth has no RMDs for you)

  ✅ FOR MAXIMIZING LEGACY TO KIDS:
     → Every dollar in Roth = 100% to kids (tax-free)
     → Every dollar in IRA = 72% to kids (after their taxes)
     → You pay 24% tax now so kids avoid 28-35% tax later
     → Path B adds ${path_b_kids_total - path_a_kids_total:,.0f} to their inheritance

  🚫 WHAT NOT TO DO:
     ✗ Don't do nothing (costs ${path_a_after_tax - path_b_after_tax:,.0f} in wealth)
     ✗ Don't use IRA money to pay conversion taxes
     ✗ Don't convert so much you deplete taxable below $125K
     ✗ Don't convert into 32% bracket (rarely worth it)

  ════════════════════════════════════════════════════════════════════════════

  🎬 NEXT STEPS:

     1. Review this plan with your financial advisor / CPA
     2. Decide on Year 1 conversion amount ($100K-$150K)
     3. Execute conversion before December 31, 2025
     4. Set aside cash for April 2026 tax payment
     5. Repeat annually, adjusting as SS begins

  ════════════════════════════════════════════════════════════════════════════

  💝 Remember: The goal isn't just numbers—it's FREEDOM and SECURITY
     for {SPOUSE1_NAME} and {SPOUSE2_NAME} now, and a meaningful legacy for your kids.

═══════════════════════════════════════════════════════════════════════════════
""")