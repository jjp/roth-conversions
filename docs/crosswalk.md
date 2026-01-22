yes, # IRS forms / worksheets crosswalk (planning model)

## Purpose

This document helps a CPA/EA reviewer map the model’s calculations and report fields to the **closest** IRS forms/worksheets concepts.

It is intentionally conservative:

- It does **not** claim the model is tax-return software.
- It does **not** guarantee line-by-line alignment with any specific tax year’s Form 1040 line numbers (those change).

For the underlying formulas and assumptions, see `docs/tax/*` and `docs/methodology/*`.

## High-level mapping

### Ordinary income tax + standard deduction

Model docs: `docs/tax/ordinary_income.md`

Closest IRS concepts:

- Form 1040 taxable income calculation (AGI minus standard deduction)
- Tax computed via rate schedules (the model uses pinned bracket schedules)

Notes:

- Model currently covers ordinary income brackets + standard deduction only.
- Preferential rates (qualified dividends/LTCG) and many credits are out of scope.

### Social Security taxable benefits

Model docs: `docs/tax/social_security_taxation.md`

Closest IRS concepts:

- IRS Publication 915 worksheets (provisional income method)
- Form 1040 Social Security benefits and taxable portion

Notes:

- Model supports MFJ and Single threshold logic; does not model MFS-with-spouse rules.

### IRA distributions, Roth conversions, and RMDs

Model docs:

- RMDs: `docs/tax/rmd.md`
- Roth 5-year approximation: `docs/tax/roth_5_year_rule.md`
- Projection ordering: `docs/methodology/projection_engine.md`

Closest IRS concepts:

- Form 1040 “IRA distributions” (gross distribution vs taxable amount)
- IRS Pub 590-B (RMD rules; Roth distribution ordering/penalties)

Notes:

- The model treats conversions as taxable ordinary income (consistent conceptually).
- Basis tracking (Form 8606) is **not** modeled.
- Roth distribution ordering is simplified; penalty exceptions are not exhaustively modeled.

### QCD (Qualified Charitable Distributions)

Model docs: `docs/tax/qcd.md`

Closest IRS concepts:

- Pub 590-B QCD rules
- Form 1040 IRA distribution reporting convention where QCD reduces taxable IRA distribution and “QCD” is noted

Notes:

- The model uses standard deduction only (it does not model itemized charitable deductions).

### NIIT (Net Investment Income Tax)

Model docs: `docs/tax/niit.md`

Closest IRS concepts:

- Form 8960 (NIIT) computation
- Carried to Form 1040 via additional taxes schedules (exact line numbers vary by year)

Notes:

- The model uses an **NII approximation** derived from taxable portfolio returns (configurable scalars).
- The model’s MAGI is a proxy based on modeled income components.

### Medicare IRMAA

Model docs: `docs/tax/irmaa.md`

Closest administrative concepts:

- SSA/CMS IRMAA determination (not an IRS form)
- Typically based on IRS-provided income information (MAGI) with a 2-year lookback

Notes:

- The model computes IRMAA as an annualized cash cost using pinned tiers and a lookback approximation.
- This is not a tax form line item.

### Heirs / inherited account distributions

Model docs: `docs/tax/heirs_distribution.md`

Closest IRS concepts:

- Pub 590-B inherited IRA distribution rules
- Form 1040 IRA distribution reporting for beneficiaries

Notes:

- The heirs module is a simplified planning overlay (flat effective tax rate; equal installment distribution).

## What “MAGI” means in this model (proxy)

The model uses a MAGI-like proxy for IRMAA and NIIT threshold logic. In `roth_conversions/projection.py` it is approximated as:

- taxable IRA withdrawals (net of QCD against RMD) + conversions + taxable Social Security + modeled investment income

This is not a full IRS MAGI definition. Reviewers should treat it as a planning approximation.

## Reviewer guidance

- Validate each component against its referenced IRS publication/form conceptually.
- Focus on (a) correctness of the implemented formulas and (b) transparency of assumptions.
- Use the report appendix “Tax Inputs & Assumptions” to confirm pinned years and configuration knobs used for a given run.
