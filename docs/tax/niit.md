# NIIT (3.8%) — calculation + NII approximation

## What this covers

This document covers how the system computes the **Net Investment Income Tax (NIIT)**.

NIIT is 3.8% applied to the lesser of:

- net investment income (NII)
- MAGI in excess of the NIIT threshold

## Implementation in this repo

- `roth_conversions/niit.py`:
  - `NIIT_RATE = 0.038`
  - `niit_threshold(filing_status)`
  - `calculate_niit(magi, net_investment_income, filing_status)`

## Calculation

1. Thresholds:
   - `MFJ`: $250,000
   - `Single`: $200,000
   - (Not inflation-indexed in the current implementation.)

2. Tax base:

   \[
   base = min(NII, max(0, MAGI - threshold))
   \]

3. Tax:

   \[
   NIIT = 0.038 \times base
   \]

## Net investment income (NII) approximation used by the projection engine

The core NIIT formula requires NII; the projection engine provides a simplified estimate derived from the taxable account return:

- `investment_income ≈ taxable_balance_for_nii × taxable_return × nii_fraction_of_return × realization_fraction`

These two scalars are configuration knobs:

- `inputs.taxes.niit_nii_fraction_of_return` (default 0.70)
- `inputs.taxes.niit_realization_fraction` (default 0.60)

## Simplifying assumptions / limitations

- NII is not modeled from detailed dividends/interest/capital gains events; it is a return-based approximation.
- NIIT thresholds are not inflation-indexed here (consistent with statutory thresholds, but always verify current law).
- MAGI is an approximation derived from the model (not a full Form 8960 computation).

## References (authoritative)

- IRS: Net Investment Income Tax overview
  - https://www.irs.gov/individuals/net-investment-income-tax
- IRS Form 8960 and instructions
  - https://www.irs.gov/forms-pubs/about-form-8960

## Auditor checklist

- Verify the threshold used for filing status.
- Verify what’s included in the model’s MAGI proxy.
- Verify NII approximation knobs and whether they are appropriate for the client’s portfolio (dividends-heavy vs growth, high turnover vs low turnover).
