# Social Security taxable benefits (provisional income)

## What this covers

This document covers how the system computes the **taxable portion of Social Security benefits** using the IRS **provisional income** method.

## Implementation in this repo

- `roth_conversions/social_security.py`:
  - `taxable_social_security(total_benefits, other_income, filing_status, tax_exempt_interest=0.0)`

## Calculation

1. Inputs:
   - `total_benefits`: annual Social Security benefits.
   - `other_income`: other income used in the simplified model (IRA withdrawals + conversions).
   - `tax_exempt_interest`: supported by the function signature but typically passed as `0.0` by the projection engine.

2. Provisional income:

   \[
   provisional = other_income + tax_exempt_interest + 0.5 \times total_benefits
   \]

3. Thresholds (current scope):
   - `MFJ`: base $32,000; adjusted base $44,000
   - `Single`: base $25,000; adjusted base $34,000

4. Taxable benefits:
   - If `provisional <= base`: taxable = 0
   - If `base < provisional <= adjusted`:
     - taxable = `0.5 * (provisional - base)` capped at `0.5 * total_benefits`
   - If `provisional > adjusted`:
     - taxable = `0.85 * (provisional - adjusted) + min(0.5*(adjusted-base), 0.5*benefits)`
     - capped at `0.85 * total_benefits`

## Simplifying assumptions / limitations

- Filing statuses handled explicitly: `MFJ`, `Single`.
- Does not model special cases such as `MFS` living with spouse.
- The projection engine uses a simplified definition of `other_income` (it does not include all possible AGI components).

## References (authoritative)

- IRS Publication 915, Social Security and Equivalent Railroad Retirement Benefits:
  - https://www.irs.gov/publications/p915

## Auditor checklist

- Verify the thresholds used for the filing status.
- Verify provisional income inputs (what the engine includes/excludes in `other_income`).
- Confirm taxable benefits are capped at 50% or 85% as applicable.
