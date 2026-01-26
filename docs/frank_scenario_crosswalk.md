# Frank Kistner comment → scenario crosswalk

This document maps Frank's notes in `comments/` to concrete scenario config files under `configs/`.

## Source comments

- `comments/frank_kistner_first.txt`
- `comments/frank_kistner_1_22_2026`
- `comments/frank_kistner_1_22_2026_implemented.md`

## Coverage map

### QCD details (age 70½, annual cap, ordering)

- Comment themes:
  - QCD eligibility is 70½
  - Annual cap ($111k referenced)
  - QCD ordering vs taxable giving
- Scenarios:
  - `configs/retirement_config.scenario_large_charity_qcd.toml` (existing)
  - `configs/retirement_config.scenario_qcd_70_5_cap_111k.toml` (explicitly sets `qcd_eligible_age=70.5`, `qcd_annual_cap_per_person=111000`)

What to validate in the packet outputs:

- In the report appendix: charity/QCD inputs reflect 70.5 + 111k.
- In yearly exports: charitable giving draws from IRA (QCD) before taxable giving where applicable.

### IRA after-tax basis + pro‑rata rule (Form 8606 concept)

- Comment themes:
  - Pro‑rata basis applies across all traditional/SEP/SIMPLE IRAs
  - Example basis $100k with total IRA $175k
- Scenarios:
  - `configs/retirement_config.scenario_ira_basis_pro_rata.toml`

What to validate:

- In yearly exports: any IRA conversion/withdrawal shows a taxable vs non-taxable split consistent with pro‑rata.

### IRMAA awareness

- Comment themes:
  - Medicare premium cliffs matter
- Scenarios:
  - `configs/retirement_config.scenario_wife_rmd_husband_no_rmd_5m_ira.toml` (existing)
  - `configs/retirement_config.scenario_widow_event_soon.toml` (existing)
  - `configs/retirement_config.scenario_large_charity_qcd.toml` (existing)

### NIIT awareness

- Comment themes:
  - NIIT thresholds and investment income taxation
- Scenarios:
  - `configs/retirement_config.scenario_niit_trigger.toml`

What to validate:

- In yearly exports: NIIT turns on in years when simplified MAGI/NIIT base exceeds threshold.

### State tax (simplified effective rate)

- Comment themes:
  - State tax can materially change optimal conversion amounts
  - Detailed state tax logic is complex; a simplified effective rate is still useful
- Scenarios:
  - `configs/retirement_config.scenario_state_tax_enabled.toml`

### Roth conversion 5‑year rule / penalties (pre‑59½)

- Comment themes:
  - Conversion principal can be subject to penalty if withdrawn within 5 years and under qualified age
- Scenarios:
  - `configs/retirement_config.scenario_roth_5yr_penalty_home_purchase.toml`

What to validate:

- In the "home purchase" output: penalty tax (if any) appears when down payment draws from recent conversions.

### Asset location (higher-growth assets in Roth)

- Comment themes:
  - Putting higher-growth assets in Roth can increase after-tax outcomes
- Scenarios:
  - `configs/retirement_config.scenario_asset_location_enabled.toml`

### Objectives / decision framework (after-tax vs legacy vs PV of taxes)

- Comment themes:
  - Optimize for different objectives (lifetime after-tax, legacy, PV of taxes)
  - Discount rate matters
  - Longevity sensitivity matters
- Scenarios:
  - `configs/retirement_config.scenario_objective_legacy.toml`
  - `configs/retirement_config.scenario_objective_npv_taxes.toml` (enables longevity sensitivity)

### Social Security taxation sensitivity

- Comment themes:
  - SS taxation can reach 85% depending on other income
- Scenarios:
  - `configs/retirement_config.scenario_ss_taxation_stress.toml`

### Heirs taxation (10-year drawdown, heir marginal rate)

- Comment themes:
  - Evaluate outcomes for heirs; heir marginal tax rate matters
- Scenarios:
  - `configs/retirement_config.scenario_no_convert_heirs_low_tax_rate.toml` (existing)

## Explicitly deferred / not modeled in detail

These are reflected in the comment docs but are not fully modeled beyond simplified approximations:

- Detailed state tax brackets, credits, and interactions
- Tax software workflow / 1099-R box-level reporting of QCD (the model focuses on tax effects, not form-filling)
