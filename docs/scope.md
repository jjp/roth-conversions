# Scope and limitations (for reviewers)

This project is a retirement projection and Roth conversion planning model intended to be **auditable** and **deterministic** under a set of explicitly stated simplifying assumptions.

## Intended validation standard

A reviewer (e.g., CPA/EA) should be able to validate that:

- each documented tax/benefit calculation follows a recognizable published rule (or a pinned table), and
- the report clearly states when the model uses an approximation.

This is not a full tax-prep system and does not attempt to produce an IRS-file-ready return.

## Major modeled components

- Federal ordinary income tax using pinned brackets + standard deduction
- Preferential tax rates for qualified dividends (QD) and long-term capital gains (LTCG) using pinned thresholds (0%/15%/20%) and worksheet-style stacking
- Optional Tier A itemized deductions (user-supplied annual amount; deduction = max(standard, itemized))
- Social Security taxation (provisional income)
- RMDs (simplified)
- Medicare Part B base premiums (pinned standard premium; simplified enrollment assumptions)
- IRMAA (pinned tiers, simplified MAGI and lookback behavior)
- NIIT (with NII approximation knobs)
- Optional simplified state income tax (flat effective rate on AGI or taxable income)
- Optional QCD, heirs modeling, widow event, Roth 5-year rule approximation

## Major exclusions (not modeled)

Ordered roughly by likely impact on IRA/Roth/RMD planning decisions (conversion “room”, marginal rates, MAGI-driven effects):

- Detailed itemized deductions (Schedule A component modeling), tax credits, and AMT
- Special preferential-rate cases (collectibles at 28%, unrecaptured §1250 gain at 25%, and other Schedule D worksheet nuances)
- State-specific retirement rules and detailed state tax law (only a simplified flat state tax is available)
- Detailed investment tax mechanics (dividend yield, turnover, tax-loss harvesting)
- Medicare enrollment timing, Part B late-enrollment penalties, and plan-specific Part D premium mechanics
- Precise Roth contribution/earnings ordering and all penalty exceptions
- Estate tax

## How to interpret outputs

Outputs are most reliable for **relative comparisons** of strategies under consistent assumptions, and as an audit-friendly approximation of the federal tax interactions that dominate Roth conversion planning.

For a single household’s actual filing, a CPA should treat outputs as planning estimates and validate any conversion plan against real tax software and current-year guidance.
