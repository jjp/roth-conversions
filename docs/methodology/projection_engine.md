# Projection engine (year-by-year cashflow + taxes)

## What this covers

This document explains the **year-by-year projection loop** used to compute balances, taxes, and summary metrics.

It does _not_ restate each tax-law formula; those are documented in `docs/tax/*`.

## Implementation in this repo

- Main engine: `roth_conversions/projection.py` (`project_with_tax_tracking`)
- Three Paths wrapper: `roth_conversions/analysis/three_paths.py`

## High-level structure (per year)

For each year $t$ in `horizon_years`:

1. Determine calendar year and ages
   - Ages increment by 1 each loop.
   - Filing status can switch to `Single` after widow event.

2. Determine Social Security income
   - SS starts at configured ages.
   - Widow simplification: survivor benefit is the larger of the two.

3. Determine annual spending need
   - Base spending is inflation-adjusted.
   - Widow simplification: spending is multiplied by `income_need_multiplier`.

4. Determine RMDs
   - Uses `roth_conversions/rmd.py`.
   - Splits IRA balance 33/67 between spouses (notebook-compatibility simplification).

5. Apply charity/QCD (optional)
   - If enabled and eligible, QCD covers part of planned charity and reduces taxable IRA withdrawal.

6. Choose withdrawals to cover remaining need (heuristic)
   - Uses a simple heuristic split across taxable, Roth, and IRA.
   - Roth withdrawals may be constrained/penalized by the Roth 5-year conversion rule model.

7. Compute taxable income and ordinary income tax
   - Standard deduction is loaded from pinned tables.
   - Taxable Social Security is computed using provisional income.
   - Ordinary income tax is computed using pinned brackets.

8. Choose Roth conversion amount (strategy-driven)
   - Strategy defines `annual_conversion`, `conversion_years`, and whether 32% is allowed.
   - Conversions are constrained by bracket ceiling room and (simplified) tax affordability.

9. Compute additional taxes/costs (optional)
   - IRMAA: uses 2-year lookback MAGI approximation.
   - NIIT: uses NII approximation derived from taxable return.

10. Pay taxes using the configured tax-payment policy

11. Apply investment returns to balances

## Key simplifying assumptions / limitations

- No state income taxes (the library engine models federal only).
- Withdrawal policy is a heuristic (not a globally optimized dynamic programming solution).
- Conversion affordability uses simplified “available cash” logic.
- RMD splitting 33/67 is a simplification.

## Reviewer checklist

- Confirm the per-year ordering (RMD/QCD/spending/conversion/taxes/returns).
- Confirm which optional modules are enabled (IRMAA/NIIT/Roth rules/charity/heirs/widow).
- Confirm pinned table year resolution behavior (see report appendix: “Tax Inputs & Assumptions”).
