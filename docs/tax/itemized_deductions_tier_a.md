# Itemized deductions (Tier A)

## What this model covers

This project supports a _Tier A_ itemized-deductions model:

- User provides a single annual itemized deduction amount.
- The tax engine uses:
  - `deduction = max(standard_deduction, itemized_deductions_annual)`

This matches the common planning question: “Will itemizing beat the standard deduction in these years?”

## Inputs

Configuration keys (under `[inputs.taxes]`):

- `itemized_deductions_enabled` (bool)
- `itemized_deductions_annual` (float, **start-year dollars**)

In each projection year, `itemized_deductions_annual` is inflated by the model’s inflation multiplier.

## Where it is implemented

- `roth_conversions/projection.py`
- `roth_conversions/analysis/home_purchase.py`

## Simplifying assumptions / exclusions

- Does not compute Schedule A lines (SALT, mortgage interest, charitable, medical, etc.).
- Does not model deduction phaseouts or AMT interactions.

Those can be added later as higher-tier itemized deduction support.
