# Documentation

This folder is written for accountants and reviewers who need to verify how each tax/benefit calculation is computed, what sources support it, and what simplifying assumptions apply.

Start here:

- [Scope and limitations (for reviewers)](scope.md)
- [IRS forms / worksheets crosswalk (planning model)](crosswalk.md)

## Core calculation notes

- [Ordinary income tax + standard deduction (pinned tables)](tax/ordinary_income.md)
- [Preferential rates (LTCG / qualified dividends) — pinned thresholds + stacking](tax/preferential_ltcg_qd.md)
- [Social Security taxable benefits (provisional income)](tax/social_security_taxation.md)
- [Medicare IRMAA (pinned tables, 2-year lookback)](tax/irmaa.md)
- [Medicare Part B base premium (pinned)](tax/medicare_part_b_base_premium.md)
- [NIIT (3.8%) — calculation + NII approximation](tax/niit.md)
- [State income tax (flat effective rate — simplified)](tax/state_flat_tax.md)
- [Itemized deductions (Tier A)](tax/itemized_deductions_tier_a.md)
- [RMDs (Uniform Lifetime Table – simplified)](tax/rmd.md)
- [QCD (modeled as RMD offset — simplified)](tax/qcd.md)
- [Roth 5-year rule for conversions (simplified penalty/prevent model)](tax/roth_5_year_rule.md)
- [Tax payment policy (taxable vs IRA gross-up)](tax/tax_payment_policy.md)
- [Heirs / inherited IRA & Roth distribution (simplified)](tax/heirs_distribution.md)

## Projection & scenario methodology

- [Projection engine (year-by-year cashflow + taxes)](methodology/projection_engine.md)
- [Three Paths (A/B/C) — strategy definitions](methodology/three_paths.md)
- [Home purchase scenario — one-time cash outflow overlay](methodology/home_purchase.md)
- [Monte Carlo (B) — correlated stock/bond simulation + charts](methodology/monte_carlo_b.md)
- [NPV and value basis (nominal vs real)](methodology/npv_and_value_basis.md)
- [Other analyses (objective selection, 32% breakeven, asset location)](methodology/other_analyses.md)

## Tax law update transparency

- [How to update pinned tax law inputs](tax/update_process.md)
- [Tax inputs changelog](tax/CHANGELOG.md)
