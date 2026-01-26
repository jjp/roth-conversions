# Frank Kistner feedback — implemented changes (2026-01-22)

Source: `comments/frank_kistner_1_22_2026`

This document summarizes which suggestions were implemented vs deferred, and where they landed in the code/config.

## Implemented

### 1) QCD eligibility age = 70½

**Suggestion:** Donor must be age 70½ or older at the time of the QCD.

**Implemented:**

- The config/model now supports a float `qcd_eligible_age` with a default of `70.5`.
- The eligibility check now compares whole-year ages against that float threshold.

**Notes / limitation:**

- The projection currently models ages in whole years, so `70.5` behaves effectively like an age-71 threshold unless the tool is extended to model DOB/month-level timing.

### 2) QCD annual cap = $111,000

**Suggestion:** There is currently a $111K annual dollar limit on QCDs.

**Implemented:**

- Default `qcd_annual_cap_per_person` is now `111000.0`.
- Cap is multiplied by covered people (`MFJ` => 2) as before.

### 3) “QCD should be taken before other IRA withdrawals”

**Suggestion:** Take QCD before other IRA withdrawals to avoid issues with treating the QCD as part of taxable distribution.

**Implemented (in-model behavior):**

- The model already treats QCD as coming out first by applying it against RMDs before taxable IRA withdrawals:
  - `qcd_from_rmd = min(qcd, total_rmd)`
  - `taxable_ira_withdrawal = (total_rmd - qcd_from_rmd) + other_withdrawals`

This preserves the intended “QCD-first” ordering inside the model’s simplified cashflow/tax logic.

### 4) Pro-rata rule when IRAs contain both pre-tax and after-tax money

**Suggestion:** Roth conversions must be pro-rata when there is after-tax basis in IRAs (Form 8606 concept). Frank provided a numeric example.

**Implemented:**

- Added a new optional input: `inputs.joint.ira_after_tax_basis` (default `0.0`).
- When `ira_after_tax_basis > 0`, the model allocates basis pro-rata across:
  - QCD distributions (basis is consumed, but QCD remains excluded from income)
  - taxable IRA withdrawals
  - Roth conversions (only the taxable portion counts toward bracket room / SS taxation / tax calculations)

**Validation:**

- Added a unit test that matches Frank’s example math.

## Deferred / Not implemented (yet)

### A) 1099-R does not identify QCD; tax software requires user worksheet adjustment

**Suggestion:** Users must properly mark QCD in tax software; simply entering 1099-R fields won’t automatically exclude QCD from income.

**Status:** Deferred.

**Why:**

- This repo is a planning/strategy engine, not a tax-form preparation workflow. There’s no 1099-R ingestion or tax-software worksheet export in the current scope.

**Good next step (if desired):**

- Add reporting text in the generated report explaining the operational tax-filing step (marking QCD on the IRA distribution worksheet / Form 1040 reporting), or add a “tax filing checklist” section.

### B) State tax spreadsheet / detailed state tax differences

**Suggestion:** State tax file is simple; incorporate state-by-state notes (7 no-income-tax states, WA capital gains, etc.).

**Status:** Deferred.

**Why:**

- The current state tax model is intentionally a flat effective rate on a chosen base; it does not attempt to model special cases like WA’s capital gains tax.

### C) First iteration: ask user for effective federal/state rates at conversion and at withdrawal

**Suggestion:** Avoid detailed tax return modeling; let user input effective rates for conversion vs withdrawal; allow multiple rates across years and for moving states.

**Status:** Deferred.

**Why:**

- This would be a significant model shift (from bracket-based tax calculation to user-supplied effective-rate overrides, possibly time-varying) and would require new config schema + UI/reporting decisions.

**Good next step (if desired):**

- Add optional override inputs like:
  - `inputs.overrides.conversion_effective_tax_rate_by_year`
  - `inputs.overrides.withdrawal_effective_tax_rate_by_year`
  - and/or “future state tax rate after move”

## Files touched (high level)

- Modeling / parsing
  - `roth_conversions/models.py` (QCD defaults; new IRA basis input)
  - `roth_conversions/config.py` (parse new defaults and basis input)

- Projection logic
  - `roth_conversions/projection.py` (QCD eligibility float; QCD cap defaults via config; pro-rata basis logic)
  - `roth_conversions/analysis/home_purchase.py` (kept consistent with projection)

- New helper + tests
  - `roth_conversions/ira_basis.py` (pro-rata allocator)
  - `tests/test_ira_basis_pro_rata.py`

- Config templates
  - `configs/retirement_config.template.toml`
  - `configs/retirement_config.example.toml`
