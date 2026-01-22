# QCD (modeled as RMD offset — simplified)

## What this covers

This document covers how the system models **Qualified Charitable Distributions (QCDs)** as a way to satisfy charitable giving while reducing taxable IRA distributions.

## Implementation in this repo

QCD behavior is implemented in the projection engine:

- `roth_conversions/projection.py`
- `roth_conversions/analysis/home_purchase.py`

Configuration:

- `inputs.charity.enabled`
- `inputs.charity.annual_amount`
- `inputs.charity.use_qcd`
- `inputs.charity.qcd_eligible_age`
- `inputs.charity.qcd_annual_cap_per_person`

## Calculation (as modeled)

- Each year, if charity is enabled, the model computes `charity_need` (inflation-adjusted).
- If `use_qcd=true` and at least one spouse meets `qcd_eligible_age`, the model sets:
  - `qcd = min(charity_need, cap, ira_balance)`
  - `cap = qcd_annual_cap_per_person × covered_people`

Then the model applies QCD against RMD first:

- `qcd_from_rmd = min(qcd, total_rmd)`
- `rmd_available_for_income = total_rmd - qcd_from_rmd`

The QCD amount reduces taxable IRA withdrawal used for SS taxation and ordinary income tax.

## Simplifying assumptions / limitations

- Eligibility uses **whole-year age** (approximation of the 70½ rule).
- The model treats QCD as if it can be used whenever eligible and does not model operational constraints.
- Does not model itemized deductions (charitable deduction) because the model uses standard deduction.

## References (authoritative)

- IRS Publication 590-B (QCD rules and reporting)
  - https://www.irs.gov/publications/p590b

## Auditor checklist

- Confirm the client’s eligibility age and annual cap under current law.
- Confirm that charitable giving in the scenario is truly intended as a QCD strategy.
- Confirm that the client’s IRA custodian and reporting requirements are met in real life (outside model scope).
