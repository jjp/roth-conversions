# Roth 5-year rule for conversions (simplified penalty/prevent model)

## What this covers

This document covers how the system models the **Roth conversion 5-year rule** risk: withdrawing converted principal “too soon” can trigger a 10% early distribution penalty if the taxpayer is not yet qualified by age.

## Implementation in this repo

- Conversion-bucket tracking + withdrawal ordering:
  - `roth_conversions/roth_rules.py`
- Applied in the projection engines:
  - `roth_conversions/projection.py`
  - `roth_conversions/analysis/home_purchase.py`

Config knobs:

- `inputs.roth_rules.enabled`
- `inputs.roth_rules.conversion_wait_years` (default 5)
- `inputs.roth_rules.qualified_age_years` (default 60; whole-year approximation of 59½)
- `inputs.roth_rules.penalty_rate` (default 0.10)
- `inputs.roth_rules.policy`:
  - `"penalty"`: allow withdrawal but add penalty
  - `"prevent"`: disallow using “young” conversion principal (forces other sources)

## Model behavior

### Ordering

The model uses a simplified ordering:

1. Starting Roth balance is treated as penalty-free “basis”.
2. Conversion buckets are consumed oldest-first.
3. Earnings are not modeled separately.

### Penalty determination

When withdrawing from conversion buckets:

- If `household_age_years < qualified_age_years` and the bucket is younger than `conversion_wait_years`, the withdrawn amount from that bucket contributes to the penalty base.
- Penalty tax added:

  \[
  penalty = penalty_rate \times penalty_base
  \]

The penalty is treated like an annual tax/expense and is paid using the configured tax payment policy.

## Simplifying assumptions / limitations

- **Contributions vs earnings vs conversions** are not tracked precisely; starting Roth is treated as penalty-free basis.
- Uses **whole-year ages** and an approximate qualified age threshold.
- This does not implement all Roth qualified distribution rules (disability, first-time home exceptions, 5-year rule for earnings, etc.).

## References (authoritative)

- IRS Publication 590-B (Roth IRA distributions; ordering; penalties)
  - https://www.irs.gov/publications/p590b

## Auditor checklist

- Confirm which policy was used (`penalty` vs `prevent`) for the run.
- Confirm conversion years and which years withdrawals occurred.
- Confirm that the simplified ordering/assumptions are acceptable for the certification scope.
