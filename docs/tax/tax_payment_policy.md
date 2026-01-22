# Tax payment policy (taxable vs IRA gross-up)

## What this covers

This document covers how the system models **where taxes are paid from**:

- taxable account (above a cash reserve), and/or
- IRA distributions with withholding “gross-up”

This matters because paying taxes from different accounts changes the future growth of each account.

## Implementation in this repo

- `roth_conversions/withdrawal_policy.py`:
  - `gross_up_for_withholding(net_tax, marginal_rate)`
  - `pay_tax(taxable, ira, tax_due, source, minimum_cash_reserve, marginal_rate)`

Config knobs:

- `inputs.withdrawal_policy.income_tax_payment_source` (`taxable` | `ira`)
- `inputs.withdrawal_policy.conversion_tax_payment_source` (`taxable` | `ira`)

## Calculation

### Paying from taxable

1. Pay from taxable cash above the reserve:
   - `available_cash = max(0, taxable - minimum_cash_reserve)`
   - `from_taxable = min(tax_due, available_cash)`
2. If taxes exceed available cash, the remainder is paid from IRA using gross-up.

### Paying from IRA (withholding gross-up)

If the marginal rate is `r`, then to net `net_tax` withheld:

\[
ira_distribution = \frac{net_tax}{1-r}
\]

The model caps `r` at 0.99 to avoid division by zero.

## Simplifying assumptions / limitations

- The gross-up uses a **single marginal-rate approximation** for the year.
- Does not model separate federal vs state withholding tables.
- Does not model quarterly estimates, safe harbors, timing differences, or penalties.

## References (authoritative)

- IRS Publication 505 (Tax Withholding and Estimated Tax)
  - https://www.irs.gov/publications/p505

## Auditor checklist

- Confirm payment sources configured for conversion tax and income tax.
- Confirm the marginal-rate input used for gross-up (as computed by the ordinary income tax model).
- Confirm cash reserve treatment for taxable-account payments.
