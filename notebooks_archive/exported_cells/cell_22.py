# =============================================================================
# 🏠 CHAPTER 8: HOME PURCHASE SCENARIO (WITH RMD CALCULATIONS)
# =============================================================================
# This analysis now includes Required Minimum Distributions (RMDs) which
# start at age 73 for both spouses. RMDs are forced withdrawals from IRAs
# that add to your taxable income whether you need the money or not.
# =============================================================================

# ┌─────────────────────────────────────────────────────────────────────────────┐
# │                    📝 CONFIGURABLE INPUT VARIABLES                         │
# └─────────────────────────────────────────────────────────────────────────────┘

# HOME_DOWN_PAYMENT: The amount needed for down payment
# - Typical range: $100K - $400K depending on home price
# - Higher = fewer funds for Roth conversion taxes
HOME_DOWN_PAYMENT = 200_000

# HOME_PURCHASE_YEAR: The calendar year you plan to buy (2025, 2026, 2027, etc.)
# - 2025: Buy immediately, fewest conversions before purchase
# - 2026: One year of conversions first, then buy
# - 2027+: More conversions before purchase, but longer wait
# 
# KEY INSIGHT: Each year you delay allows ~$100K-150K MORE in conversions
# because you still have full taxable account to pay conversion taxes.
HOME_PURCHASE_YEAR = 2027  # Enter the actual calendar year

# Calculate offset from base year (2025 = Year 1)
BASE_YEAR = 2025
PURCHASE_YEAR_OFFSET = HOME_PURCHASE_YEAR - BASE_YEAR  # 0 for 2025, 1 for 2026, etc.

# =============================================================================
# RMD TABLE (IRS Uniform Lifetime Table - ages 72-95)
# =============================================================================
RMD_DIVISORS = {
    72: 27.4, 73: 26.5, 74: 25.5, 75: 24.6, 76: 23.7, 77: 22.9, 78: 22.0,
    79: 21.1, 80: 20.2, 81: 19.4, 82: 18.5, 83: 17.7, 84: 16.8, 85: 16.0,
    86: 15.2, 87: 14.4, 88: 13.7, 89: 12.9, 90: 12.2, 91: 11.5, 92: 10.8,
    93: 10.1, 94: 9.5, 95: 8.9
}

def get_rmd_divisor(age):
    """Get RMD divisor for a given age"""
    if age < 73:
        return None  # No RMD required
    return RMD_DIVISORS.get(age, 8.9)  # Use 8.9 for ages 95+

def calculate_rmd(ira_balance, age):
    """Calculate Required Minimum Distribution"""
    divisor = get_rmd_divisor(age)
    if divisor is None:
        return 0
    return ira_balance / divisor

# =============================================================================
# ENHANCED PROJECTION FUNCTION WITH RMDs
# =============================================================================

def project_with_rmds(purchase_year_offset, down_payment, initial_ira, initial_roth, 
                      initial_taxable, conversion_years=5, max_annual_conv=150_000):
    """
    Enhanced projection that includes RMD calculations.
    
    Parameters:
    -----------
    purchase_year_offset : int
        Years from 2025 to buy home (0 = 2025, 1 = 2026, etc.)
    down_payment : float
        Down payment amount
    initial_ira, initial_roth, initial_taxable : float
        Starting balances
    conversion_years : int
        How many years to do conversions
    max_annual_conv : float
        Maximum conversion per year
    
    Returns detailed year-by-year breakdown including RMDs.
    """
    
    # Track balances
    ira = initial_ira
    roth = initial_roth
    taxable = initial_taxable
    
    # Results tracking
    total_conversions = 0
    total_rmds = 0
    total_rmd_tax = 0
    conversion_schedule = []
    rmd_schedule = []
    yearly_data = []
    
    # Ages at start (2025)
    rajesh_age_start = SPOUSE1_AGE  # 60
    terri_age_start = SPOUSE2_AGE   # 61
    
    # Split calculation for home purchase
    split_taxable = min(down_payment // 2, taxable - MINIMUM_CASH_RESERVE)
    split_ira_net = down_payment - split_taxable
    split_ira_gross = split_ira_net * 1.24  # Add 24% for tax
    
    for yr in range(25):
        rajesh_age = rajesh_age_start + yr
        terri_age = terri_age_start + yr
        year_data = {'year': yr + 1, 'calendar_year': 2025 + yr}
        
        # === BEGINNING OF YEAR ===
        year_data['ira_start'] = ira
        year_data['roth_start'] = roth
        year_data['taxable_start'] = taxable
        
        # === RMD CALCULATIONS ===
        # RMDs are based on prior year-end balance, but we'll use current for simplicity
        rajesh_rmd = calculate_rmd(ira * 0.33, rajesh_age)  # ~1/3 is Rajesh's
        terri_rmd = calculate_rmd(ira * 0.67, terri_age)    # ~2/3 is Terri's
        total_rmd_this_year = rajesh_rmd + terri_rmd
        
        # RMDs come out of IRA
        ira -= total_rmd_this_year
        total_rmds += total_rmd_this_year
        
        # RMD tax (at ~24% marginal rate)
        rmd_tax = total_rmd_this_year * 0.24
        total_rmd_tax += rmd_tax
        
        year_data['rajesh_age'] = rajesh_age
        year_data['terri_age'] = terri_age
        year_data['rmd'] = total_rmd_this_year
        year_data['rmd_tax'] = rmd_tax
        rmd_schedule.append(total_rmd_this_year)
        
        # === HOME PURCHASE ===
        home_this_year = (yr == purchase_year_offset)
        if home_this_year:
            taxable -= split_taxable
            ira -= split_ira_gross
            year_data['home_purchase'] = True
            year_data['home_from_taxable'] = split_taxable
            year_data['home_from_ira'] = split_ira_gross
        else:
            year_data['home_purchase'] = False
        
        # === ROTH CONVERSIONS ===
        conversion = 0
        if yr < conversion_years:
            # How much can we convert?
            available_for_tax = taxable - MINIMUM_CASH_RESERVE
            
            # Before home purchase, also reserve the down payment
            if yr < purchase_year_offset:
                available_for_tax -= down_payment
            
            if available_for_tax > 0:
                # Max conversion based on available tax funds
                max_from_funds = available_for_tax / 0.24
                
                # Reduced conversion in home purchase year (IRA withdrawal uses bracket space)
                if home_this_year:
                    max_this_year = 75_000
                else:
                    max_this_year = max_annual_conv
                
                conversion = min(max_from_funds, max_this_year, ira)
                conversion = max(0, conversion)
        
        # Execute conversion
        if conversion > 0:
            conv_tax = conversion * 0.24
            ira -= conversion
            roth += conversion
            taxable -= conv_tax
            total_conversions += conversion
        
        conversion_schedule.append(conversion)
        year_data['conversion'] = conversion
        year_data['conv_tax'] = conversion * 0.24 if conversion > 0 else 0
        
        # === INCOME NEEDS ===
        income_need = ANNUAL_INCOME_NEED * (1 + INFLATION_RATE) ** yr
        ss1 = SPOUSE1_SS_ANNUAL if yr >= years_to_rajesh_ss else 0
        ss2 = SPOUSE2_SS_ANNUAL if yr >= years_to_terri_ss else 0
        total_ss = ss1 + ss2
        
        # RMDs count as income (can cover some needs)
        from_rmd_for_spending = min(total_rmd_this_year * 0.76, income_need - total_ss)  # After tax
        remaining_need = max(0, income_need - total_ss - from_rmd_for_spending)
        
        # Draw from accounts for remaining need
        from_taxable = min(remaining_need * 0.3, taxable - MINIMUM_CASH_RESERVE)
        from_roth = min(remaining_need * 0.2, roth)
        from_ira = remaining_need - from_taxable - from_roth
        
        taxable -= max(0, from_taxable)
        roth -= max(0, from_roth)
        ira -= max(0, from_ira * 1.24)  # Gross up for tax
        
        year_data['income_need'] = income_need
        year_data['ss_income'] = total_ss
        
        # === GROWTH ===
        ira *= (1 + IRA_RETURN)
        roth *= (1 + ROTH_RETURN)
        taxable *= (1 + TAXABLE_RETURN)
        
        # === END OF YEAR ===
        year_data['ira_end'] = ira
        year_data['roth_end'] = roth
        year_data['taxable_end'] = taxable
        
        yearly_data.append(year_data)
    
    # Final calculations
    after_tax = ira * 0.75 + roth + taxable * 0.92
    legacy = ira * (1 - 0.28) + roth + taxable * 0.95
    
    return {
        'total_conversions': total_conversions,
        'total_rmds': total_rmds,
        'total_rmd_tax': total_rmd_tax,
        'conversion_schedule': conversion_schedule,
        'rmd_schedule': rmd_schedule,
        'yearly_data': yearly_data,
        'ira': ira,
        'roth': roth,
        'taxable': taxable,
        'after_tax': after_tax,
        'legacy': legacy
    }

# =============================================================================
# RUN THE ANALYSIS
# =============================================================================

print("═" * 80)
print(f"🏠 CHAPTER 8: HOME PURCHASE ANALYSIS (${HOME_DOWN_PAYMENT:,} DOWN PAYMENT)")
print(f"   📅 Planned Purchase: {HOME_PURCHASE_YEAR} (Year {PURCHASE_YEAR_OFFSET + 1} of retirement)")
print(f"   📊 NOW INCLUDES RMD CALCULATIONS!")
print("═" * 80)

# Run scenarios
no_home = project_with_rmds(99, 0, TOTAL_PRETAX, TOTAL_ROTH, JOINT_TAXABLE_ACCOUNTS)
buy_2025 = project_with_rmds(0, HOME_DOWN_PAYMENT, TOTAL_PRETAX, TOTAL_ROTH, JOINT_TAXABLE_ACCOUNTS)
buy_2026 = project_with_rmds(1, HOME_DOWN_PAYMENT, TOTAL_PRETAX, TOTAL_ROTH, JOINT_TAXABLE_ACCOUNTS)
buy_2027 = project_with_rmds(2, HOME_DOWN_PAYMENT, TOTAL_PRETAX, TOTAL_ROTH, JOINT_TAXABLE_ACCOUNTS)
selected = project_with_rmds(PURCHASE_YEAR_OFFSET, HOME_DOWN_PAYMENT, TOTAL_PRETAX, TOTAL_ROTH, JOINT_TAXABLE_ACCOUNTS)

print(f"""
┌─────────────────────────────────────────────────────────────────────────────┐
│                         YOUR SITUATION                                      │
└─────────────────────────────────────────────────────────────────────────────┘

  💵 Down Payment Needed:    ${HOME_DOWN_PAYMENT:>12,}
  📅 Planned Purchase Year:  {HOME_PURCHASE_YEAR}
  
  📊 Current Assets:
     ├── Taxable Account:    ${JOINT_TAXABLE_ACCOUNTS:>12,}
     ├── IRAs (pre-tax):     ${TOTAL_PRETAX:>12,}
     └── Roth IRAs:          ${TOTAL_ROTH:>12,}

  ⏰ RMD Timeline:
     ├── {SPOUSE2_NAME} turns 73:     {2025 + years_to_terri_rmd - 1} - RMDs begin
     └── {SPOUSE1_NAME} turns 73:    {2025 + years_to_rajesh_rmd - 1} - RMDs begin
""")

# RMD ANALYSIS
print("""
┌─────────────────────────────────────────────────────────────────────────────┐
│              📊 RMD IMPACT: WHY THIS MATTERS FOR HOME PURCHASE              │
└─────────────────────────────────────────────────────────────────────────────┘
""")

print(f"""
  🔴 WITHOUT HOME PURCHASE (Maximum Conversions):
     • Total Roth Conversions:  ${no_home['total_conversions']:>12,.0f}
     • Total RMDs over 25 yrs:  ${no_home['total_rmds']:>12,.0f}
     • RMD Tax Paid:            ${no_home['total_rmd_tax']:>12,.0f}
  
  🏠 WITH HOME PURCHASE IN {HOME_PURCHASE_YEAR}:
     • Total Roth Conversions:  ${selected['total_conversions']:>12,.0f}  ({selected['total_conversions'] - no_home['total_conversions']:+,.0f})
     • Total RMDs over 25 yrs:  ${selected['total_rmds']:>12,.0f}  ({selected['total_rmds'] - no_home['total_rmds']:+,.0f})
     • RMD Tax Paid:            ${selected['total_rmd_tax']:>12,.0f}  ({selected['total_rmd_tax'] - no_home['total_rmd_tax']:+,.0f})

  💡 KEY INSIGHT: 
     Fewer conversions → Larger IRA → Higher RMDs → More forced income → More tax
""")

# TIMING COMPARISON
print("""
┌─────────────────────────────────────────────────────────────────────────────┐
│              📅 TIMING COMPARISON: WHEN TO BUY THE HOME                     │
└─────────────────────────────────────────────────────────────────────────────┘
""")

print(f"""
╔═════════════════════════╦══════════════╦══════════════╦══════════════╦══════════════╗
║                         ║   NO HOME    ║  BUY 2025    ║  BUY 2026    ║  BUY 2027    ║
║       METRIC            ║  (Baseline)  ║   (Year 1)   ║   (Year 2)   ║   (Year 3)   ║
╠═════════════════════════╬══════════════╬══════════════╬══════════════╬══════════════╣
║ Roth Conversions        ║ ${no_home['total_conversions']:>10,.0f}  ║ ${buy_2025['total_conversions']:>10,.0f}  ║ ${buy_2026['total_conversions']:>10,.0f}  ║ ${buy_2027['total_conversions']:>10,.0f}  ║
║ Total RMDs (25 yrs)     ║ ${no_home['total_rmds']:>10,.0f}  ║ ${buy_2025['total_rmds']:>10,.0f}  ║ ${buy_2026['total_rmds']:>10,.0f}  ║ ${buy_2027['total_rmds']:>10,.0f}  ║
║ RMD Tax Paid            ║ ${no_home['total_rmd_tax']:>10,.0f}  ║ ${buy_2025['total_rmd_tax']:>10,.0f}  ║ ${buy_2026['total_rmd_tax']:>10,.0f}  ║ ${buy_2027['total_rmd_tax']:>10,.0f}  ║
╠═════════════════════════╬══════════════╬══════════════╬══════════════╬══════════════╣
║ 25-Year Wealth          ║ ${no_home['after_tax']:>10,.0f}  ║ ${buy_2025['after_tax']:>10,.0f}  ║ ${buy_2026['after_tax']:>10,.0f}  ║ ${buy_2027['after_tax']:>10,.0f}  ║
║ Legacy to Kids          ║ ${no_home['legacy']:>10,.0f}  ║ ${buy_2025['legacy']:>10,.0f}  ║ ${buy_2026['legacy']:>10,.0f}  ║ ${buy_2027['legacy']:>10,.0f}  ║
╠═════════════════════════╬══════════════╬══════════════╬══════════════╬══════════════╣
║ vs No Home              ║ $         0  ║ ${buy_2025['after_tax'] - no_home['after_tax']:>+10,.0f}  ║ ${buy_2026['after_tax'] - no_home['after_tax']:>+10,.0f}  ║ ${buy_2027['after_tax'] - no_home['after_tax']:>+10,.0f}  ║
║ vs Buy 2025             ║      ---     ║ $         0  ║ ${buy_2026['after_tax'] - buy_2025['after_tax']:>+10,.0f}  ║ ${buy_2027['after_tax'] - buy_2025['after_tax']:>+10,.0f}  ║
╚═════════════════════════╩══════════════╩══════════════╩══════════════╩══════════════╝
""")

# YEAR BY YEAR FOR SELECTED TIMING
print(f"""
┌─────────────────────────────────────────────────────────────────────────────┐
│    📅 YOUR PLAN: BUY IN {HOME_PURCHASE_YEAR} - YEAR-BY-YEAR BREAKDOWN{'':>26}│
└─────────────────────────────────────────────────────────────────────────────┘
""")

print("  Year  Calendar  Ages    Conversion    RMD         Notes")
print("  ────  ────────  ─────   ──────────    ──────────  ─────────────────────")
for i, yd in enumerate(selected['yearly_data'][:15]):  # Show first 15 years
    ages = f"{yd['rajesh_age']}/{yd['terri_age']}"
    conv = f"${yd['conversion']:>9,.0f}" if yd['conversion'] > 0 else "         -"
    rmd = f"${yd['rmd']:>9,.0f}" if yd['rmd'] > 0 else "         -"
    
    notes = []
    if yd.get('home_purchase'):
        notes.append("🏠 BUY HOME")
    if yd['terri_age'] == 73:
        notes.append(f"{SPOUSE2_NAME} RMD starts")
    if yd['rajesh_age'] == 73:
        notes.append(f"{SPOUSE1_NAME} RMD starts")
    if i + 1 == years_to_terri_ss:
        notes.append(f"{SPOUSE2_NAME} SS +${SPOUSE2_SS_ANNUAL:,}")
    if i + 1 == years_to_rajesh_ss:
        notes.append(f"{SPOUSE1_NAME} SS +${SPOUSE1_SS_ANNUAL:,}")
    
    note_str = ", ".join(notes) if notes else ""
    print(f"  {yd['year']:>4}  {yd['calendar_year']:>8}  {ages:<6}  {conv}    {rmd}  {note_str}")

print(f"""
  ... (Years 16-25 continue with RMDs and growth)

  ═══════════════════════════════════════════════════════════════════════════
  TOTALS (25 years):
     • Total Conversions: ${selected['total_conversions']:>12,.0f}
     • Total RMDs:        ${selected['total_rmds']:>12,.0f}
     • Total RMD Tax:     ${selected['total_rmd_tax']:>12,.0f}
  ═══════════════════════════════════════════════════════════════════════════
""")

# RECOMMENDATION
print("""
┌─────────────────────────────────────────────────────────────────────────────┐
│                       🎯 RECOMMENDATION                                     │
└─────────────────────────────────────────────────────────────────────────────┘
""")

best_option = max([(buy_2025, 2025), (buy_2026, 2026), (buy_2027, 2027)], key=lambda x: x[0]['after_tax'])
best_result, best_year = best_option
benefit_vs_2025 = best_result['after_tax'] - buy_2025['after_tax']

print(f"""
  📊 ANALYSIS SUMMARY (with ${HOME_DOWN_PAYMENT:,} down payment):

  ✅ BEST TIMING: Buy in {best_year}
     • 25-Year Wealth:        ${best_result['after_tax']:>12,.0f}
     • Legacy to Kids:        ${best_result['legacy']:>12,.0f}
     • Total Roth Conversions:${best_result['total_conversions']:>12,.0f}
     • Total RMDs:            ${best_result['total_rmds']:>12,.0f}
""")

if best_year > 2025:
    print(f"""
  💰 VALUE OF WAITING TO {best_year}:
     • Extra wealth vs 2025:   ${benefit_vs_2025:>+12,.0f}
     • Extra conversions:      ${best_result['total_conversions'] - buy_2025['total_conversions']:>+12,.0f}
     • Lower RMDs:             ${best_result['total_rmds'] - buy_2025['total_rmds']:>+12,.0f}
     
  WHY? Delaying allows more Roth conversions BEFORE the down payment
  depletes your taxable account. More conversions = lower IRA = lower RMDs
  = less forced taxable income later.
""")

# Cost of home vs no home
cost_of_home = no_home['after_tax'] - best_result['after_tax']
print(f"""
  🏠 TOTAL COST OF BUYING THE HOME:
     • Wealth reduction vs no home: ${cost_of_home:>12,.0f}
     • That's ${cost_of_home/25:,.0f}/year in lost wealth accumulation
     • BUT: You get a home! Quality of life has value too.

  ⚠️  LIFE CONSIDERATIONS:
     • Can you wait until {best_year} to buy?
     • Are home prices rising faster than your gains from waiting?
     • What's the rental/housing cost while waiting?
     • Is there a perfect home available NOW?

  🔧 TO EXPLORE: Change HOME_DOWN_PAYMENT (amount) and HOME_PURCHASE_YEAR 
     (2025, 2026, 2027, etc.) at the top of this cell and re-run.
""")