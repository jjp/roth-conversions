# Tax inputs changelog

This changelog tracks changes to pinned tax/benefit inputs and any related calculation logic.

## Unreleased

### Pinned ordinary income tax tables

- Pinned years available: 2024, 2025, 2026
- Files:
  - `roth_conversions/data/tax/us_federal_ordinary_income_2024.json`
  - `roth_conversions/data/tax/us_federal_ordinary_income_2025.json`
  - `roth_conversions/data/tax/us_federal_ordinary_income_2026.json`
- Sources (per file metadata):
  - 2024: IRS newsroom release (references Rev. Proc. 2023-34)
    - https://www.irs.gov/newsroom/irs-provides-tax-inflation-adjustments-for-tax-year-2024
  - 2025: IRS newsroom release (IR-2024-273) + Rev. Proc. 2024-40 PDF
    - https://www.irs.gov/newsroom/irs-releases-tax-inflation-adjustments-for-tax-year-2025
    - https://www.irs.gov/pub/irs-drop/rp-24-40.pdf
  - 2026: IRS newsroom release + Rev. Proc. 2025-32 PDF
    - https://www.irs.gov/newsroom/irs-releases-tax-inflation-adjustments-for-tax-year-2026-including-amendments-from-the-one-big-beautiful-bill
    - https://www.irs.gov/pub/irs-drop/rp-25-32.pdf

### Pinned IRMAA tables

- Pinned years available: 2025, 2026
- Files:
  - `roth_conversions/data/medicare/irmaa_2025.json`
  - `roth_conversions/data/medicare/irmaa_2026.json`
- Sources (per file metadata):
  - 2025: CMS fact sheet
    - https://www.cms.gov/newsroom/fact-sheets/2025-medicare-parts-b-premiums-and-deductibles
  - 2026: SSA Medicare premiums page
    - https://www.ssa.gov/benefits/medicare/medicare-premiums.html

### Pinned Medicare Part B base premium

- Pinned years available: 2025, 2026
- Files:
  - `roth_conversions/data/medicare/part_b_base_premium_2025.json`
  - `roth_conversions/data/medicare/part_b_base_premium_2026.json`
- Sources (per file metadata):
  - 2025: CMS fact sheet
    - https://www.cms.gov/newsroom/fact-sheets/2025-medicare-parts-b-premiums-and-deductibles
  - 2026: SSA Medicare premiums page
    - https://www.ssa.gov/benefits/medicare/medicare-premiums.html

### Auditability supporting changes (tied to these inputs)

- Added “golden” tests that lock in selected pinned-table values and resolution behavior:
  - `tests/test_pinned_tables_golden.py`
- Added a report appendix section “Tax Inputs & Assumptions” that prints resolved pinned years and key knobs:
  - `roth_conversions/reporting/builder.py`

## Template for annual update

### Tax year YYYY (ordinary income tax + standard deduction)

- Sources:
  - IRS Rev. Proc. YYYY-XX: <url>
- Updated files:
  - `roth_conversions/data/tax/us_federal_ordinary_income_YYYY.json`
- Notes:
  - (bracket threshold changes, standard deduction changes, filing statuses supported)

### Premium year YYYY (IRMAA)

- Sources:
  - SSA/CMS IRMAA table: <url>
- Updated files:
  - `roth_conversions/data/medicare/irmaa_YYYY.json`
- Notes:
  - (tier thresholds, monthly add-ons)
