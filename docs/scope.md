# Scope and limitations (for reviewers)

This project is a retirement projection and Roth conversion planning model intended to be **auditable** and **deterministic** under a set of explicitly stated simplifying assumptions.

## Intended validation standard

A reviewer (e.g., CPA/EA) should be able to validate that:

- each documented tax/benefit calculation follows a recognizable published rule (or a pinned table), and
- the report clearly states when the model uses an approximation.

This is not a full tax-prep system and does not attempt to produce an IRS-file-ready return.

## Major modeled components

- Federal ordinary income tax using pinned brackets + standard deduction
- Social Security taxation (provisional income)
- RMDs (simplified)
- IRMAA (pinned tiers, simplified MAGI and lookback behavior)
- NIIT (with NII approximation knobs)
- Optional QCD, heirs modeling, widow event, Roth 5-year rule approximation

## Major exclusions (not modeled)

- State income taxes and state-specific retirement rules
- Preferential capital gains / qualified dividends tax rates
- Itemized deductions, credits, AMT
- Medicare base premiums (only IRMAA add-ons are modeled)
- Detailed investment tax mechanics (dividend yield, turnover, tax-loss harvesting)
- Precise Roth contribution/earnings ordering and all penalty exceptions
- Estate tax

## How to interpret outputs

Outputs are most reliable for **relative comparisons** of strategies under consistent assumptions, and as an audit-friendly approximation of the federal tax interactions that dominate Roth conversion planning.

For a single household’s actual filing, a CPA should treat outputs as planning estimates and validate any conversion plan against real tax software and current-year guidance.
