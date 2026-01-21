# IRS tax data: what we download, what we pin, how it’s processed

This repo intentionally avoids “guessing” federal ordinary income brackets and the standard deduction.
Instead, it **pins** the tax tables into versioned JSON files sourced from IRS publications.

## What is pinned (used at runtime)

Runtime uses these files:

- `roth_conversions/data/tax/us_federal_ordinary_income_2024.json`
- `roth_conversions/data/tax/us_federal_ordinary_income_2025.json`
- `roth_conversions/data/tax/us_federal_ordinary_income_2026.json`

Each file contains:

- `tax_year`
- `ordinary_income.brackets` (by filing status; currently `MFJ` and `Single`)
- `ordinary_income.standard_deduction` (by filing status)
- `metadata.source` (URL + publication info)

These pinned files are read by `roth_conversions/tax_tables.py`.

### Why we pin

- Deterministic runs (no network calls at runtime)
- Easy auditing: the numbers are visible in-repo
- Easy updates: add a new JSON file per year

## What we download (reference material)

We keep the source PDFs in `data/irs_sources/` for traceability:

- `rp-23-34.pdf` (Rev. Proc. 2023-34; tax year 2024 adjustments)
- `rp-24-40.pdf` (Rev. Proc. 2024-40; tax year 2025 adjustments)
- `rp-25-32.pdf` (Rev. Proc. 2025-32; tax year 2026 adjustments)

These PDFs are **not parsed at runtime**.

## Social Security taxation

Social Security taxable benefits are modeled via the **provisional income** method in:

- `roth_conversions/social_security.py`

The projection engine calls this instead of assuming “85% taxable” for every case.

## Tax payment source (withdrawal policy)

The model supports paying **income tax** and/or **conversion tax** from either:

- taxable accounts (respecting `minimum_cash_reserve`, then spilling over to IRA if needed), or
- the IRA.

When taxes are paid from the IRA, the projection uses a **marginal-rate gross-up approximation** to estimate how large a pre-tax IRA distribution must be to net a given tax payment via withholding.

This is intentionally a simplification: it does **not** iterate to account for the additional taxable income created by the grossed-up distribution itself.

## How updates work (script)

Helper script:

- `scripts/update_irs_tax_tables.py`

What it does:

1. Fetches the IRS newsroom page for a given tax year (defaults are built-in for 2024–2026).
2. Extracts standard deduction + bracket thresholds via regex.
3. Writes/overwrites `roth_conversions/data/tax/us_federal_ordinary_income_<YEAR>.json`.

Example:

- `python scripts/update_irs_tax_tables.py --tax-year 2025`

Optional: also download a Rev. Proc PDF into `data/irs_sources/`:

- `python scripts/update_irs_tax_tables.py --tax-year 2026 --rev-proc-url https://www.irs.gov/pub/irs-drop/rp-25-32.pdf`

### Notes / limitations

- The script is a **helper**, not a contract. IRS newsroom pages can change formatting.
- If parsing fails, update the pinned JSON manually (and keep the source URL in `metadata`).
- 2026 IRS guidance includes legislative amendments and also mentions updated 2025 standard deduction amounts; reconcile year-to-year changes based on the latest official guidance you want the model to reflect.
