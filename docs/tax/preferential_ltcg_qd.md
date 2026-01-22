# Preferential tax rates: LTCG / qualified dividends

## What this model covers

This project models U.S. federal **preferential tax rates** for:

- **Qualified dividends (QD)**
- **Long-term capital gains (LTCG)**

These amounts are taxed at **0% / 15% / 20%** depending on **total taxable income** and filing status.

This is implemented as a _planning model_ (not a full return-prep engine).

## Pinned inputs (tables)

We pin the **maximum 0% rate amount** and **maximum 15% rate amount** (expressed as total taxable income thresholds).

Files:

- `roth_conversions/data/tax/us_federal_preferential_income_2024.json`
- `roth_conversions/data/tax/us_federal_preferential_income_2025.json`
- `roth_conversions/data/tax/us_federal_preferential_income_2026.json`

Source:

- Rev. Proc. 2023-34 (TY 2024): https://www.irs.gov/pub/irs-drop/rp-23-34.pdf
- Rev. Proc. 2024-40 (TY 2025): https://www.irs.gov/pub/irs-drop/rp-24-40.pdf
- Rev. Proc. 2025-32 (TY 2026): https://www.irs.gov/pub/irs-drop/rp-25-32.pdf

### Year resolution policy

For a requested tax year, the model uses:

- **latest pinned year ≤ requested year**

This matches the project’s ordinary-income table resolution policy.

Code:

- `roth_conversions/tax_tables.py`: `resolve_preferential_tax_year()`, `get_ltcg_qd_thresholds()`

## How tax is computed (worksheet-style stacking)

Inputs (conceptual):

- `ordinary_income` (IRA withdrawals, Roth conversions, taxable SS, etc.)
- `qualified_dividends`
- `long_term_capital_gains`
- `deduction` (standard or itemized)

Steps:

1. Compute total taxable income:
   - `taxable_income = max(0, ordinary_income + QD + LTCG - deduction)`

2. Compute the portion eligible for preferential rates:
   - `preferential_taxable = min(QD + LTCG, taxable_income)`

3. Ordinary taxable portion:
   - `ordinary_taxable = taxable_income - preferential_taxable`

4. Ordinary tax is computed using pinned ordinary brackets on `ordinary_taxable`.

5. Preferential tax uses the pinned thresholds (expressed as taxable income cutoffs):
   - 0% applies to the portion of preferential income that fits under the 0% threshold _after_ ordinary taxable income fills the bottom.
   - 15% applies to the next portion of preferential income up to the 15% threshold.
   - 20% applies above the 15% threshold.

Code:

- `roth_conversions/tax.py`: `calculate_tax_federal_ltcg_qd_simple()`

## Simplifying assumptions / exclusions

- Does not model collectibles (28%) and unrecaptured §1250 gain (25%).
- Does not model the full Schedule D worksheet nuances.
- Treats QD + LTCG as the only preferential-rate base.

These simplifications are acceptable for many Roth-conversion planning comparisons, but can be material in certain households.
