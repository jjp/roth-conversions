# Three Paths (A/B/C) — strategy definitions

## What this covers

This document explains how the report’s “Three Paths (A/B/C)” are defined.

## Implementation in this repo

- `roth_conversions/analysis/three_paths.py` (`run_three_paths`)
- Underlying per-year engine: `roth_conversions/projection.py` (`project_with_tax_tracking`)

## Path definitions

The Three Paths analysis produces three projections using the same household inputs and horizon:

- Path A: **Do Nothing**
  - `annual_conversion = 0`
  - `conversion_years = 0`

- Path B: **Smart Convert** (default parameters)
  - `annual_conversion = 100,000`
  - `conversion_years = 5`

- Path C: **Aggressive** (default parameters)
  - `annual_conversion = 150,000`
  - `conversion_years = 10`

These are _default_ analysis parameters; other report sections may use additional named strategies.

## Conversion constraints

The engine constrains conversions to avoid exceeding a chosen bracket ceiling:

- Default constraint is “stay within 24%” unless the strategy explicitly allows 32%.
- Bracket ceilings are retrieved from pinned tax tables (or fall back to historical constants if unavailable).

## Outputs used by reporting

Each path returns summary metrics such as:

- `after_tax` / `legacy` / `heirs_after_tax`
- totals for conversion tax, RMD tax, IRMAA cost, NIIT, Roth penalty
- PV taxes/spending (in start-year dollars)

## Reviewer checklist

- Confirm which path parameters (annual amount, years) were used in the report run.
- Confirm bracket ceiling policy (≤24% vs allow 32%).
- Confirm that all three paths share the same starting balances, assumptions, and horizon.
