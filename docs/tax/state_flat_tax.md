# State income tax (flat effective rate — simplified)

## What this module models

This project can optionally model a **simple state income tax** as a flat effective rate applied to an income base.

This is meant for planning comparisons only.

## Calculation

Let:

- $r$ = state flat tax rate (e.g., 0.05 for 5%)
- $B$ = chosen base

Then:

$$\text{StateTax} = r \times \max(0, B)$$

### Supported bases

- `agi`: uses the model’s internal AGI/MAGI approximation:
  - IRA withdrawals + conversions + taxable Social Security + modeled (realized) taxable investment income.
- `taxable_income`: uses **federal taxable income** as computed in the model (after standard deduction).

## Simplifying assumptions / limitations

- Does not model state-specific brackets, deductions, credits, AMT, reciprocity, local taxes, or special retirement rules.
- Does not model SALT deductibility or other interactions between federal and state taxes.
- Intended to be a _single_ tunable planning knob.

## Configuration

In TOML under `inputs.taxes`:

- `state_tax_enabled` (bool)
- `state_tax_rate` (float in [0, 1])
- `state_tax_base` (`"agi"` or `"taxable_income"`)

## Where implemented

- Config parsing: `roth_conversions/config.py`
- Main projection: `roth_conversions/projection.py`
- Home purchase scenario: `roth_conversions/analysis/home_purchase.py`
