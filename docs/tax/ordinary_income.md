# Ordinary income tax + standard deduction (pinned tables)

## What this covers

This document covers how the system calculates **U.S. federal ordinary income tax** and the **standard deduction** used by the projection engine.

## Implementation in this repo

- Pinned bracket tables + standard deduction:
  - `roth_conversions/data/tax/us_federal_ordinary_income_*.json`
  - Loaded via `roth_conversions/tax_tables.py`
- Tax computation:
  - `roth_conversions/tax_tables.calculate_tax()`
  - Public wrapper: `roth_conversions/tax.calculate_tax_ordinary_income()`

## Calculation

1. Resolve the table year:
   - `resolve_tax_year(requested_year)` chooses the latest pinned year **<=** the requested year.
   - This makes projections deterministic if a future year’s tables are not yet pinned.

2. Standard deduction:
   - `get_standard_deduction(tax_year, filing_status)` reads the pinned value.

3. Taxable income (engine-level):
   - The projection engine builds a taxable-income figure and then calls `calculate_tax_ordinary_income(taxable_income, tax_year, filing_status)`.

4. Bracket tax:
   - A simple progressive, piecewise function applies each bracket rate to income within that bracket.

## Simplifying assumptions / limitations

- Only **ordinary income** brackets are modeled (no preferential rates for LTCG/qualified dividends).
- The system currently supports filing statuses present in the pinned tables (commonly `MFJ` and `Single`).
- The codebase uses **standard deduction only** (no itemized deductions).
- Credits (CTC, education credits, etc.), AMT, and other special taxes are not modeled.

## References (authoritative)

Because tax parameters change annually, the system uses pinned tables sourced from IRS annual inflation-adjustment guidance.

- IRS “Inflation Adjustments” Revenue Procedures (examples already stored in `data/irs_sources/`):
  - Rev. Proc. 2023-34 (tax year 2024 inflation adjustments): https://www.irs.gov/pub/irs-drop/rp-23-34.pdf
  - Rev. Proc. 2024-40 (tax year 2025 inflation adjustments): https://www.irs.gov/pub/irs-drop/rp-24-40.pdf
  - Rev. Proc. 2025-32 (tax year 2026 inflation adjustments): https://www.irs.gov/pub/irs-drop/rp-25-32.pdf

## Auditor checklist

- Confirm which pinned year was used for a given run (requested year vs resolved year).
- Confirm brackets + standard deduction match the cited Revenue Procedure for that tax year.
- Confirm filing status used in each year (widow event can switch to `Single`).
