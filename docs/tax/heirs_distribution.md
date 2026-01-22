# Heirs / inherited IRA & Roth distribution (simplified)

## What this covers

This document covers the system’s simplified modeling of **after-tax value to heirs** when inherited retirement accounts must be distributed within a fixed window.

## Implementation in this repo

- `roth_conversions/heirs.py`:
  - `simulate_inherited_distribution_after_tax(...)`
  - `simulate_inherited_roth_after_tax(...)`

Used by:

- `roth_conversions/projection.py` (end-of-horizon calculation of `heirs_after_tax`)

Config knobs:

- `inputs.heirs.enabled`
- `inputs.heirs.distribution_years` (commonly 5 or 10)
- `inputs.heirs.heir_tax_rate` (flat effective tax rate)

## Model behavior

- The inherited account grows at the configured return.
- The beneficiary withdraws in equal installments to fully distribute by the end of the window.
- For inherited **traditional** IRA:
  - each withdrawal is taxed at `heir_tax_rate` (flat)
  - after-tax proceeds are reinvested in taxable at `beneficiary_taxable_return`
- For inherited **Roth**:
  - withdrawals are treated as tax-free in this model
  - proceeds are reinvested similarly

The function returns the beneficiary’s taxable balance after the distribution window.

## Simplifying assumptions / limitations

- Uses equal annual distributions; does not model “end of year 10” lump sum behavior.
- Uses a flat effective heir tax rate (not a bracketed tax computation).
- Does not model required minimum distributions for inherited accounts by beneficiary type.
- Roth inherited withdrawals are treated as tax-free without modeling qualified distribution rules.

## References (authoritative)

- IRS Publication 590-B (inherited IRA rules and distribution requirements)
  - https://www.irs.gov/publications/p590b

## Auditor checklist

- Confirm the correct rule window (e.g., 10-year rule for many non-spouse beneficiaries) for the client’s facts.
- Confirm the assumed heir tax rate is defensible.
- Confirm whether equal installments are acceptable for the certification scope.
