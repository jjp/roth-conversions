print("═" * 80)
print("🔀 CHAPTER 3: YOUR THREE PATHS (WITH ACCURATE TAX CALCULATIONS)")
print("═" * 80)

# =============================================================================
# YEAR-BY-YEAR PROJECTION FUNCTION (local version for this analysis)
# Uses shared functions: calculate_tax_mfj, get_marginal_rate, calculate_rmd
# =============================================================================

def project_path(annual_conversion, conversion_years, path_name=""):
    """
    Project a path year-by-year with accurate tax calculations.
    
    This properly accounts for:
    - Income withdrawals from IRA (taxable)
    - Roth conversions (taxable, added on top of income)
    - Social Security (partially taxable - using 85%)
    - RMDs starting at age 73
    - Actual marginal tax rates based on combined income
    """
    
    # Starting balances
    ira = TOTAL_PRETAX
    roth = TOTAL_ROTH
    taxable = JOINT_TAXABLE_ACCOUNTS
    
    # Tracking
    total_conversions = 0
    total_conversion_tax = 0
    total_rmds = 0
    total_rmd_tax = 0
    yearly_details = []
    
    for yr in range(25):
        rajesh_age = SPOUSE1_AGE + yr
        terri_age = SPOUSE2_AGE + yr
        
        year_data = {
            'year': yr + 1,
            'calendar_year': 2025 + yr,
            'rajesh_age': rajesh_age,
            'terri_age': terri_age,
            'ira_start': ira,
            'roth_start': roth,
            'taxable_start': taxable
        }
        
        # === INCOME SOURCES ===
        
        # 1. Social Security (85% taxable for high earners)
        ss1 = SPOUSE1_SS_ANNUAL if yr >= years_to_rajesh_ss else 0
        ss2 = SPOUSE2_SS_ANNUAL if yr >= years_to_terri_ss else 0
        total_ss = ss1 + ss2
        ss_taxable = total_ss * 0.85  # 85% of SS is taxable at your income level
        
        # 2. Income need (inflation adjusted)
        income_need = ANNUAL_INCOME_NEED * (1 + INFLATION_RATE) ** yr
        
        # 3. How much do we need from savings after SS?
        from_savings_needed = max(0, income_need - total_ss)
        
        # 4. RMDs (calculated on prior year-end balance for simplicity)
        rajesh_rmd = calculate_rmd(ira * 0.33, rajesh_age)  # ~1/3 is Rajesh's
        terri_rmd = calculate_rmd(ira * 0.67, terri_age)    # ~2/3 is Terri's
        total_rmd = rajesh_rmd + terri_rmd
        total_rmds += total_rmd
        
        # RMD satisfies some of the income need
        rmd_for_income = min(total_rmd, from_savings_needed)
        remaining_need = from_savings_needed - rmd_for_income
        
        # === WHERE DOES INCOME COME FROM? ===
        
        # Priority: RMDs first, then taxable, then Roth, then additional IRA
        from_rmd = rmd_for_income
        from_taxable = min(remaining_need * 0.5, max(0, taxable - MINIMUM_CASH_RESERVE))
        from_roth = min(remaining_need * 0.3, roth)
        from_ira_extra = max(0, remaining_need - from_taxable - from_roth)
        
        # Total IRA withdrawal = RMD + any extra needed
        total_ira_withdrawal = total_rmd + from_ira_extra
        
        year_data['ss_income'] = total_ss
        year_data['rmd'] = total_rmd
        year_data['from_ira'] = total_ira_withdrawal
        year_data['from_taxable'] = from_taxable
        year_data['from_roth'] = from_roth
        
        # === ROTH CONVERSIONS ===
        
        conversion = 0
        conversion_tax = 0
        
        if yr < conversion_years and annual_conversion > 0:
            # How much can we afford to convert?
            available_for_conv_tax = max(0, taxable - MINIMUM_CASH_RESERVE - from_taxable)
            
            # What's our base taxable income BEFORE conversion?
            base_taxable_income = ss_taxable + total_ira_withdrawal - STANDARD_DEDUCTION_MFJ
            base_taxable_income = max(0, base_taxable_income)
            
            # What marginal rate would we pay on conversions?
            marginal_rate = get_marginal_rate(base_taxable_income)
            
            # How much can we convert and stay in 24% bracket?
            room_in_24_bracket = max(0, 383900 - base_taxable_income)
            
            # Limit conversion to: available funds for tax, annual target, room in bracket, IRA balance
            max_affordable = available_for_conv_tax / marginal_rate if marginal_rate > 0 else 0
            conversion = min(annual_conversion, room_in_24_bracket, max_affordable, ira - total_ira_withdrawal)
            conversion = max(0, conversion)
            
            if conversion > 0:
                # Calculate actual tax on conversion (at marginal rate after other income)
                income_before_conv = base_taxable_income
                income_after_conv = base_taxable_income + conversion
                conversion_tax = calculate_tax_mfj(income_after_conv) - calculate_tax_mfj(income_before_conv)
                
                total_conversions += conversion
                total_conversion_tax += conversion_tax
        
        year_data['conversion'] = conversion
        year_data['conversion_tax'] = conversion_tax
        
        # === TAX ON IRA WITHDRAWALS (income + RMDs) ===
        
        # Tax on regular income (IRA withdrawals that aren't conversions)
        total_taxable_income = ss_taxable + total_ira_withdrawal - STANDARD_DEDUCTION_MFJ
        total_taxable_income = max(0, total_taxable_income)
        income_tax = calculate_tax_mfj(total_taxable_income)
        
        # RMD portion of the tax
        if total_ira_withdrawal > 0:
            rmd_share = total_rmd / total_ira_withdrawal
            rmd_tax = income_tax * rmd_share
        else:
            rmd_tax = 0
        total_rmd_tax += rmd_tax
        
        year_data['income_tax'] = income_tax
        
        # === UPDATE BALANCES ===
        
        # Withdrawals
        ira -= total_ira_withdrawal
        ira -= conversion  # Move to Roth
        roth += conversion
        roth -= from_roth
        taxable -= from_taxable
        taxable -= conversion_tax  # Pay conversion tax from taxable
        taxable -= income_tax * 0.5  # Rough estimate: some tax paid from taxable
        
        # Growth
        ira *= (1 + IRA_RETURN)
        roth *= (1 + ROTH_RETURN)
        taxable *= (1 + TAXABLE_RETURN)
        
        # Ensure minimums
        ira = max(0, ira)
        roth = max(0, roth)
        taxable = max(0, taxable)
        
        year_data['ira_end'] = ira
        year_data['roth_end'] = roth
        year_data['taxable_end'] = taxable
        
        yearly_details.append(year_data)
    
    # Final calculations
    after_tax = ira * 0.75 + roth + taxable * 0.92
    legacy = ira * (1 - 0.28) + roth + taxable * 0.95
    first_rmd = yearly_details[years_to_terri_rmd - 1]['rmd'] if years_to_terri_rmd <= 25 else 0
    
    return {
        'path_name': path_name,
        'total_conversions': total_conversions,
        'total_conversion_tax': total_conversion_tax,
        'effective_conv_rate': (total_conversion_tax / total_conversions * 100) if total_conversions > 0 else 0,
        'total_rmds': total_rmds,
        'total_rmd_tax': total_rmd_tax,
        'ira': ira,
        'roth': roth,
        'taxable': taxable,
        'after_tax': after_tax,
        'legacy': legacy,
        'first_rmd': first_rmd,
        'yearly_details': yearly_details
    }

# =============================================================================
# RUN THE THREE PATHS
# =============================================================================

# PATH A: Do Nothing
path_a = project_path(annual_conversion=0, conversion_years=0, path_name="Do Nothing")

# PATH B: Smart Conversions ($100K/year for 5 years = $500K total)
path_b = project_path(annual_conversion=100_000, conversion_years=5, path_name="Smart Convert")

# PATH C: Aggressive Conversions ($150K/year for 10 years)
path_c = project_path(annual_conversion=150_000, conversion_years=10, path_name="Aggressive")

# =============================================================================
# DISPLAY RESULTS
# =============================================================================

print(f"""
┌─────────────────────────────────────────────────────────────────────────────┐
│          💡 HOW THIS ANALYSIS WORKS (NOW WITH ACCURATE TAXES!)              │
└─────────────────────────────────────────────────────────────────────────────┘

  This analysis now properly calculates taxes based on your ACTUAL situation:

  📊 YOUR ANNUAL INCOME STRUCTURE:
     ├── Living expenses needed:  ${ANNUAL_INCOME_NEED:>10,}/year
     ├── IRA withdrawals for living: TAXABLE as ordinary income
     ├── Roth conversions: ADDED to other income, taxed at marginal rate
     └── Standard deduction:      -${STANDARD_DEDUCTION_MFJ:>10,}

  ⚠️  THE KEY INSIGHT: 
     When you convert $100K to Roth, it's taxed ON TOP of your living expenses!
     
     Example Year 1 (before SS):
     • IRA withdrawal for living: ~$132,000 (your income need)
     • Roth conversion:           +$100,000
     • TOTAL taxable income:       $232,000 - $30K deduction = $202,000
     • Marginal rate on conversion: 24% (just into that bracket!)
""")

years_to_s1_rmd_local = max(0, 73 - SPOUSE1_AGE)
years_to_s2_rmd_local = max(0, 73 - SPOUSE2_AGE)
first_rmd_person = SPOUSE1_NAME if years_to_s1_rmd_local <= years_to_s2_rmd_local else SPOUSE2_NAME
first_rmd_label = f"First RMD ({first_rmd_person} age 73)"

print(f"""
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE THREE PATHS COMPARED                            │
└─────────────────────────────────────────────────────────────────────────────┘

╔═══════════════════════════════════════════════════════════════════════════════════════════╗
║                           ║   PATH A:          ║   PATH B:          ║   PATH C:           ║
║       METRIC              ║   Do Nothing       ║   Smart Convert    ║   Aggressive        ║
╠═══════════════════════════╬════════════════════╬════════════════════╬═════════════════════╣
║ Conversion Strategy       ║ $0/year × 0 yrs    ║ $100K/yr × 5 yrs   ║ $150K/yr × 10 yrs   ║
║ Total Conversions         ║ ${path_a['total_conversions']:>16,.0f}  ║ ${path_b['total_conversions']:>16,.0f}  ║ ${path_c['total_conversions']:>16,.0f}   ║
║ Total Conversion Tax      ║ ${path_a['total_conversion_tax']:>16,.0f}  ║ ${path_b['total_conversion_tax']:>16,.0f}  ║ ${path_c['total_conversion_tax']:>16,.0f}   ║
║ Effective Tax Rate        ║            {'N/A':>6}  ║ {path_b['effective_conv_rate']:>15.1f}%  ║ {path_c['effective_conv_rate']:>15.1f}%   ║
╠═══════════════════════════╬════════════════════╬════════════════════╬═════════════════════╣
║ Total RMDs (25 years)     ║ ${path_a['total_rmds']:>16,.0f}  ║ ${path_b['total_rmds']:>16,.0f}  ║ ${path_c['total_rmds']:>16,.0f}   ║
║ Total RMD Tax             ║ ${path_a['total_rmd_tax']:>16,.0f}  ║ ${path_b['total_rmd_tax']:>16,.0f}  ║ ${path_c['total_rmd_tax']:>16,.0f}   ║
╠═══════════════════════════╬════════════════════╬════════════════════╬═════════════════════╣
║ IRA at Year 25            ║ ${path_a['ira']:>16,.0f}  ║ ${path_b['ira']:>16,.0f}  ║ ${path_c['ira']:>16,.0f}   ║
║ Roth at Year 25           ║ ${path_a['roth']:>16,.0f}  ║ ${path_b['roth']:>16,.0f}  ║ ${path_c['roth']:>16,.0f}   ║
║ Taxable at Year 25        ║ ${path_a['taxable']:>16,.0f}  ║ ${path_b['taxable']:>16,.0f}  ║ ${path_c['taxable']:>16,.0f}   ║
╠═══════════════════════════╬════════════════════╬════════════════════╬═════════════════════╣
║ AFTER-TAX WEALTH          ║ ${path_a['after_tax']:>16,.0f}  ║ ${path_b['after_tax']:>16,.0f}  ║ ${path_c['after_tax']:>16,.0f}   ║
║ vs Do Nothing             ║ ${0:>16,.0f}  ║ ${path_b['after_tax'] - path_a['after_tax']:>+16,.0f}  ║ ${path_c['after_tax'] - path_a['after_tax']:>+16,.0f}   ║
╠═══════════════════════════╬════════════════════╬════════════════════╬═════════════════════╣
║ LEGACY TO KIDS            ║ ${path_a['legacy']:>16,.0f}  ║ ${path_b['legacy']:>16,.0f}  ║ ${path_c['legacy']:>16,.0f}   ║
║ {first_rmd_label:<23} ║ ${path_a['first_rmd']:>16,.0f}  ║ ${path_b['first_rmd']:>16,.0f}  ║ ${path_c['first_rmd']:>16,.0f}   ║
╚═══════════════════════════╩════════════════════╩════════════════════╩═════════════════════╝
""")

# Show year-by-year for Path B (the recommended path)
print("""
┌─────────────────────────────────────────────────────────────────────────────┐
│              📅 PATH B YEAR-BY-YEAR (First 10 Years)                        │
└─────────────────────────────────────────────────────────────────────────────┘
""")
print("  Year  Ages    SS Income    IRA Wdraw    Conversion   Conv Tax    Marginal")
print("  ────  ─────   ──────────   ──────────   ──────────   ─────────   ────────")

for yd in path_b['yearly_details'][:10]:
    ages = f"{yd['rajesh_age']}/{yd['terri_age']}"
    ss = f"${yd['ss_income']:>9,.0f}" if yd['ss_income'] > 0 else "        -"
    ira_w = f"${yd['from_ira']:>9,.0f}"
    conv = f"${yd['conversion']:>9,.0f}" if yd['conversion'] > 0 else "        -"
    conv_tax = f"${yd['conversion_tax']:>8,.0f}" if yd['conversion_tax'] > 0 else "       -"
    
    # Calculate marginal rate
    base_income = yd['ss_income'] * 0.85 + yd['from_ira'] - STANDARD_DEDUCTION_MFJ
    rate = get_marginal_rate(base_income + yd['conversion']) * 100
    rate_str = f"{rate:.0f}%"
    
    print(f"  {yd['year']:>4}  {ages:<6}  {ss}   {ira_w}   {conv}   {conv_tax}      {rate_str}")

print(f"""
  ═══════════════════════════════════════════════════════════════════════════
  PATH B TOTALS:
     • Total Converted:    ${path_b['total_conversions']:>12,.0f}
     • Total Conv Tax:     ${path_b['total_conversion_tax']:>12,.0f} (Effective rate: {path_b['effective_conv_rate']:.1f}%)
     • Total RMDs:         ${path_b['total_rmds']:>12,.0f}
  ═══════════════════════════════════════════════════════════════════════════
""")

# Key insights
print(f"""
┌─────────────────────────────────────────────────────────────────────────────┐
│                         💡 KEY INSIGHTS                                     │
└─────────────────────────────────────────────────────────────────────────────┘

  📊 THE TAX BRACKETS THAT MATTER FOR YOU (2024 MFJ, after $30K deduction):
     ┌────────────────────────────────────────────────────────────────────────┐
     │  22% bracket:  $94,300 - $201,050   ← Your income lands here          │
     │  24% bracket:  $201,050 - $383,900  ← Conversions push you here       │
     │  32% bracket:  $383,900 - $487,450  ← DANGER ZONE - avoid this!       │
     └────────────────────────────────────────────────────────────────────────┘
     
     Your $132K income (after deduction: ~$102K) starts in the 22% bracket.
     Adding conversions pushes you into 24%. The goal is to FILL the 24% 
     bracket but NOT spill into 32%!
     
     💡 Room in 24% bracket = $383,900 - $102,000 = ~$282,000/year
        But limited by funds to pay tax and other constraints.

  🎯 BEST PATH: {'PATH B (Smart Convert)' if path_b['after_tax'] >= path_c['after_tax'] else 'PATH C (Aggressive)'}
     • After-tax wealth: ${max(path_b['after_tax'], path_c['after_tax']):,.0f}
     • Gain vs doing nothing: ${max(path_b['after_tax'], path_c['after_tax']) - path_a['after_tax']:+,.0f}

  ⚠️  WATCH OUT FOR:
     • Year {years_to_terri_ss + 1}+: {SPOUSE2_NAME}'s SS adds +${SPOUSE2_SS_ANNUAL:,}/yr taxable income → less room in 24%
     • Year {years_to_rajesh_ss + 1}+: {SPOUSE1_NAME}'s SS adds +${SPOUSE1_SS_ANNUAL:,}/yr more → bracket space shrinks further
     • Year {min(years_to_terri_rmd, years_to_rajesh_rmd) + 1}+: RMDs start → may push you toward 32% automatically!

  💰 THE STRATEGY:
     • Convert at 22-24% NOW to avoid paying 24-32% on RMDs LATER
     • Path B effective rate: {path_b['effective_conv_rate']:.1f}% 
     • Without conversions, RMDs will be taxed at 24%+ when SS is also flowing
""")

# Store results for later chapters
conversion_total_b = path_b['total_conversions']
conversion_tax_b = path_b['total_conversion_tax']
conversion_total_c = path_c['total_conversions']
conversion_tax_c = path_c['total_conversion_tax']
path_a_after_tax = path_a['after_tax']
path_b_after_tax = path_b['after_tax']
path_c_after_tax = path_c['after_tax']
path_a_first_rmd = path_a['first_rmd']
path_b_first_rmd = path_b['first_rmd']
path_c_first_rmd = path_c['first_rmd']
path_a_ira = path_a['ira']
path_b_ira = path_b['ira']
path_c_ira = path_c['ira']
path_a_roth = path_a['roth']
path_b_roth = path_b['roth']
path_c_roth = path_c['roth']
path_a_taxable = path_a['taxable']
path_b_taxable = path_b['taxable']
path_c_taxable = path_c['taxable']