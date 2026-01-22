# Medicare IRMAA (pinned tables, 2-year lookback)

## What this covers

This document covers how the system estimates **Medicare IRMAA** (Income-Related Monthly Adjustment Amount) as an annual cost.

Important: IRMAA is modeled here as **monthly add-ons** only. The **standard Part B base premium** (the amount everyone pays before IRMAA) is modeled separately when enabled.

IRMAA affects:

- Medicare Part B premium (IRMAA add-on)
- Medicare Part D premium (IRMAA add-on)

## Implementation in this repo

- Pinned IRMAA tables:
  - `roth_conversions/data/medicare/irmaa_*.json`
  - Loaded via `roth_conversions/irmaa_tables.py`
- Lookup:
  - `get_irmaa_addons_monthly(premium_year, filing_status, magi) -> (part_b_add, part_d_add)`

Related (base premium, optional):

- Part B base premium tables:
  - `roth_conversions/data/medicare/part_b_base_premium_*.json`
  - Loaded via `roth_conversions/medicare_part_b_tables.py`
- Documentation:
  - `docs/tax/medicare_part_b_base_premium.md`

## Calculation

1. The engine computes a proxy for MAGI (see assumptions below).
2. IRMAA is determined using a **2-year lookback**:
   - for `premium_year = Y`, it looks at `magi` from `Y-2` when available.
3. The table returns **monthly add-ons** (not base premiums).
4. The projection annualizes the add-on and multiplies by covered people:
   - `covered_people = 2` for `MFJ`, else `1`
   - `annual_irmaa_cost = (part_b_add + part_d_add) * 12 * covered_people`

## Simplifying assumptions / limitations

- Uses a **MAGI approximation** derived from the model’s income components (IRA withdrawals, conversions, taxable SS, and the model’s investment-income approximation).
- Does not model SSA/CMS determinations, appeals, or life-changing event relief.
- Uses pinned IRMAA tables with “latest pinned year <= requested year” resolution, similar to the tax tables.
- Treats IRMAA as a cash expense paid from taxable (then IRA spillover per tax payment policy).

## References (authoritative)

- Medicare.gov: IRMAA overview
  - https://www.medicare.gov/basics/costs/medicare-costs
- SSA: Medicare Part B premiums / IRMAA information (varies by year)
  - https://www.ssa.gov/benefits/medicare/

(Exact dollar tiers change annually; the pinned JSON should be traceable to the published SSA/CMS tables used for that year.)

## Auditor checklist

- Confirm the premium year used and the lookback year MAGI value.
- Confirm filing status used in that year (widow event can switch to `Single`).
- Confirm the pinned tier thresholds and add-ons match the published IRMAA table for the premium year.
