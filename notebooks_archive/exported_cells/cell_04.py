# =============================================================================
# INPUTS (SAMPLE DATA): edit ONLY the INPUTS dictionary below
# =============================================================================

# Sample placeholder values:
# - Change names, ages, balances, and SS settings to match your household
# - Everything else in the notebook reads from these inputs

INPUTS = {
    # Household info
    "household": {
        "tax_filing_status": "MFJ",  # this notebook currently assumes Married Filing Jointly brackets
        "start_year": 2025,
    },
    # Spouse 1 (NOT yet at RMD age)
    "spouse1": {
        "name": "Spouse 1",
        "age": 70,
        "traditional_ira": 900_000,
        "sep_ira": 0,
        "roth_ira": 50_000,
        "ss_start_age": 70,
        "ss_annual": 48_000,
    },
    # Spouse 2 (already at/over RMD age)
    "spouse2": {
        "name": "Spouse 2",
        "age": 75,
        "traditional_ira": 1_150_000,
        "sep_ira": 0,
        "roth_ira": 100_000,
        "ss_start_age": 68,
        "ss_annual": 28_000,
    },
    # Joint accounts
    "joint": {
        "taxable_accounts": 450_000,
    },
    # Spending / cash
    "plan": {
        "monthly_income_need": 10_000,
        "minimum_cash_reserve": 75_000,
    },
    # Assumptions
    "assumptions": {
        "inflation_rate": 0.025,
        "taxable_return": 0.060,
        "ira_return": 0.060,
        "roth_return": 0.070,
    },
}

# =============================================================================
# VALIDATION (light sanity checks)
# =============================================================================

def _require_non_negative(value, label: str) -> None:
    if value is None:
        raise ValueError(f"{label} is missing")
    if value < 0:
        raise ValueError(f"{label} must be >= 0 (got {value})")

def _require_positive(value, label: str) -> None:
    if value is None:
        raise ValueError(f"{label} is missing")
    if value <= 0:
        raise ValueError(f"{label} must be > 0 (got {value})")

def _require_non_empty(value, label: str) -> None:
    if value is None or (isinstance(value, str) and value.strip() == ""):
        raise ValueError(f"{label} is missing")

_require_non_empty(INPUTS["spouse1"]["name"], "spouse1.name")
_require_positive(INPUTS["spouse1"]["age"], "spouse1.age")
_require_non_negative(INPUTS["spouse1"]["traditional_ira"], "spouse1.traditional_ira")
_require_non_negative(INPUTS["spouse1"]["sep_ira"], "spouse1.sep_ira")
_require_non_negative(INPUTS["spouse1"]["roth_ira"], "spouse1.roth_ira")
_require_positive(INPUTS["spouse1"]["ss_start_age"], "spouse1.ss_start_age")
_require_non_negative(INPUTS["spouse1"]["ss_annual"], "spouse1.ss_annual")

_require_non_empty(INPUTS["spouse2"]["name"], "spouse2.name")
_require_positive(INPUTS["spouse2"]["age"], "spouse2.age")
_require_non_negative(INPUTS["spouse2"]["traditional_ira"], "spouse2.traditional_ira")
_require_non_negative(INPUTS["spouse2"]["sep_ira"], "spouse2.sep_ira")
_require_non_negative(INPUTS["spouse2"]["roth_ira"], "spouse2.roth_ira")
_require_positive(INPUTS["spouse2"]["ss_start_age"], "spouse2.ss_start_age")
_require_non_negative(INPUTS["spouse2"]["ss_annual"], "spouse2.ss_annual")

_require_non_negative(INPUTS["joint"]["taxable_accounts"], "joint.taxable_accounts")
_require_positive(INPUTS["plan"]["monthly_income_need"], "plan.monthly_income_need")
_require_non_negative(INPUTS["plan"]["minimum_cash_reserve"], "plan.minimum_cash_reserve")

_require_positive(INPUTS["assumptions"]["inflation_rate"], "assumptions.inflation_rate")
_require_positive(INPUTS["assumptions"]["taxable_return"], "assumptions.taxable_return")
_require_positive(INPUTS["assumptions"]["ira_return"], "assumptions.ira_return")
_require_positive(INPUTS["assumptions"]["roth_return"], "assumptions.roth_return")

# =============================================================================
# BACKWARD-COMPAT VARIABLES (so the rest of the notebook runs unchanged)
# =============================================================================

# --- SPOUSE 1 ---
SPOUSE1_NAME = INPUTS["spouse1"]["name"]
SPOUSE1_AGE = INPUTS["spouse1"]["age"]
SPOUSE1_TRADITIONAL_IRA = INPUTS["spouse1"]["traditional_ira"]
SPOUSE1_SEP_IRA = INPUTS["spouse1"]["sep_ira"]
SPOUSE1_ROTH_IRA = INPUTS["spouse1"]["roth_ira"]
SPOUSE1_SS_START_AGE = INPUTS["spouse1"]["ss_start_age"]
SPOUSE1_SS_ANNUAL = INPUTS["spouse1"]["ss_annual"]  # Social Security at claiming age

# --- SPOUSE 2 ---
SPOUSE2_NAME = INPUTS["spouse2"]["name"]
SPOUSE2_AGE = INPUTS["spouse2"]["age"]
SPOUSE2_TRADITIONAL_IRA = INPUTS["spouse2"]["traditional_ira"]
SPOUSE2_SEP_IRA = INPUTS["spouse2"]["sep_ira"]
SPOUSE2_ROTH_IRA = INPUTS["spouse2"]["roth_ira"]
SPOUSE2_SS_START_AGE = INPUTS["spouse2"]["ss_start_age"]
SPOUSE2_SS_ANNUAL = INPUTS["spouse2"]["ss_annual"]

# --- JOINT ACCOUNTS ---
JOINT_TAXABLE_ACCOUNTS = INPUTS["joint"]["taxable_accounts"]

# --- YOUR NEEDS ---
MONTHLY_INCOME_NEED = INPUTS["plan"]["monthly_income_need"]
ANNUAL_INCOME_NEED = MONTHLY_INCOME_NEED * 12
MINIMUM_CASH_RESERVE = INPUTS["plan"]["minimum_cash_reserve"]

# --- ASSUMPTIONS ---
INFLATION_RATE = INPUTS["assumptions"]["inflation_rate"]
TAXABLE_RETURN = INPUTS["assumptions"]["taxable_return"]
IRA_RETURN = INPUTS["assumptions"]["ira_return"]
ROTH_RETURN = INPUTS["assumptions"]["roth_return"]

# Calculate totals
SPOUSE1_PRETAX = SPOUSE1_TRADITIONAL_IRA + SPOUSE1_SEP_IRA
SPOUSE2_PRETAX = SPOUSE2_TRADITIONAL_IRA + SPOUSE2_SEP_IRA
TOTAL_PRETAX = SPOUSE1_PRETAX + SPOUSE2_PRETAX
TOTAL_ROTH = SPOUSE1_ROTH_IRA + SPOUSE2_ROTH_IRA
TOTAL_WEALTH = TOTAL_PRETAX + TOTAL_ROTH + JOINT_TAXABLE_ACCOUNTS

print("═" * 80)
print("📍 CHAPTER 1: WHERE YOU STAND TODAY")
print("═" * 80)
print(f"""
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HOUSEHOLD BALANCE SHEET                             │
└─────────────────────────────────────────────────────────────────────────────┘

  👨 {SPOUSE1_NAME} (Age {SPOUSE1_AGE})
     ├── Traditional IRA:  ${SPOUSE1_TRADITIONAL_IRA:>12,.0f}
     ├── SEP IRA:          ${SPOUSE1_SEP_IRA:>12,.0f}
     ├── Roth IRA:         ${SPOUSE1_ROTH_IRA:>12,.0f}
     └── SUBTOTAL:         ${SPOUSE1_PRETAX:>12,.0f}

  👩 {SPOUSE2_NAME} (Age {SPOUSE2_AGE})
     ├── Traditional IRA:  ${SPOUSE2_TRADITIONAL_IRA:>12,.0f}
     ├── SEP IRA:          ${SPOUSE2_SEP_IRA:>12,.0f}
     ├── Roth IRA:         ${SPOUSE2_ROTH_IRA:>12,.0f}
     └── SUBTOTAL:         ${SPOUSE2_PRETAX:>12,.0f}

  🏦 Joint Taxable:        ${JOINT_TAXABLE_ACCOUNTS:>12,.0f}

  ════════════════════════════════════════════════════════════════════
  💰 TOTAL WEALTH:         ${TOTAL_WEALTH:>12,.0f}
  ════════════════════════════════════════════════════════════════════

  📊 ASSET ALLOCATION:
     • Pre-Tax (IRA/SEP):  ${TOTAL_PRETAX:>10,.0f}  ({TOTAL_PRETAX/TOTAL_WEALTH:.0%}) ← Uncle Sam's share here
     • Tax-Free (Roth):    ${TOTAL_ROTH:>10,.0f}  ({TOTAL_ROTH/TOTAL_WEALTH:.0%})
     • Taxable:            ${JOINT_TAXABLE_ACCOUNTS:>10,.0f}  ({JOINT_TAXABLE_ACCOUNTS/TOTAL_WEALTH:.0%})

  ⚠️  THE PROBLEM: {TOTAL_PRETAX/TOTAL_WEALTH:.0%} of your wealth is in PRE-TAX accounts.
     Every dollar withdrawn will be taxed as ordinary income!
""")