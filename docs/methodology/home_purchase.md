# Home purchase scenario — one-time cash outflow overlay

## What this covers

This document explains the “Home Purchase Scenario” analysis and how it changes the projection compared to the baseline engine.

## Implementation in this repo

- `roth_conversions/analysis/home_purchase.py` (`project_with_home_purchase`)

## Scenario definition

Inputs:

- `purchase_year` (calendar year)
- `down_payment` (cash outflow in purchase year)

The scenario simulates the household for `horizon_years` and applies a **one-time** cash need in the purchase year.

## Home purchase drawdown ordering (as modeled)

In the purchase year, the down payment is sourced in this order:

1. Taxable account above the minimum cash reserve (net of regular spending draws)
2. Roth account
3. IRA account

If Roth rules are enabled, Roth withdrawals for the home purchase also follow the simplified Roth 5-year conversion policy (penalty or prevent).

## Taxes and interactions

- Regular annual taxes still apply (ordinary income, SS taxation, NIIT/IRMAA if enabled).
- The home purchase itself is treated purely as a cash outflow; it does not create mortgage interest deductions or property tax deductions.

## Simplifying assumptions / limitations

- No mortgage modeling.
- No housing appreciation / ongoing property tax / insurance / maintenance.
- Tax effects are limited to the withdrawal consequences needed to raise cash.

## Reviewer checklist

- Confirm purchase year offset relative to `inputs.household.start_year`.
- Confirm down payment amount.
- Confirm drawdown ordering and interaction with Roth rules.
