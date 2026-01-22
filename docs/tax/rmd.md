# RMDs (Uniform Lifetime Table – simplified)

## What this covers

This document covers how the system computes **Required Minimum Distributions (RMDs)** from pre-tax IRA balances.

## Implementation in this repo

- `roth_conversions/rmd.py`:
  - `rmd_divisor(age)`
  - `required_minimum_distribution(ira_balance, age)`

## Calculation

- If `age < 73`: RMD = 0
- Else:

  \[
  RMD = \frac{IRA_balance}{Uniform\ Lifetime\ divisor(age)}
  \]

The divisor is taken from a hard-coded table for ages 72–95; for ages > 95 the code uses a constant fallback divisor of 8.9.

## Simplifying assumptions / limitations

- Uses a simplified start-age rule (`< 73` => 0). This matches the current notebook logic but may not cover all cohorts.
- Uses a partial divisor table and a fallback for age > 95.
- Does not model multiple accounts and precise IRS aggregation rules.

## References (authoritative)

- IRS Publication 590-B (Distributions from Individual Retirement Arrangements)
  - https://www.irs.gov/publications/p590b

## Auditor checklist

- Verify the client’s RMD start age under current law.
- Verify the divisors match the correct IRS Uniform Lifetime Table for the applicable year.
- Confirm whether special rules apply (spouse >10 years younger, inherited accounts, etc.).
