# How to update pinned tax law inputs (and keep changes transparent)

## Goal

Accountants will need to certify outputs. This system should make it obvious:

- which law/table versions were used,
- which sources support them,
- what changed between versions,
- and what tests prove the implementation still behaves as expected.

This document describes a practical, low-friction process to keep tax law updates transparent.

## 1) Pin tax-law inputs (never “scrape live” at runtime)

The current design is correct for auditability:

- Ordinary income tax & standard deduction are pinned in JSON (`roth_conversions/data/tax/`).
- IRMAA tiers are pinned in JSON (`roth_conversions/data/medicare/`).

Recommendation: keep following this pattern for all law-driven inputs.

### Why

- Deterministic runs: re-running a client case next month should produce the same result unless you intentionally update the pinned tables.
- Repeatability: auditors can reproduce the exact calculation.

## 2) Add metadata alongside each pinned table

For each pinned JSON file, add fields like:

- `effective_tax_year` / `effective_premium_year`
- `source_name` (e.g., “Rev. Proc. 2025-32”)
- `source_url`
- `retrieved_at` (ISO date)
- `notes`

(Do not copy/paste large IRS tables into docs; keep the authoritative PDF as the source and store only the numeric thresholds needed.)

## 3) Keep a human-readable changelog

Create/maintain a simple markdown file such as:

- `docs/tax/CHANGELOG.md`

For each year update, record:

- which JSON files changed
- which source PDF/URL supports the new values
- any logic changes (not just parameter changes)
- which tests were added/updated

## 4) Add “golden tests” for each major computation

Add unit tests that validate:

- bracket tax for a few known taxable-income points
- standard deduction values for the year/status
- SS taxable benefit edge cases
- NIIT threshold behavior and base calculation
- IRMAA tier selection for known MAGI points

These tests should be small and “obviously correct” so an accountant can reason about them.

## 5) Version the tax policy used by a report

Recommendation: whenever you generate a report, include a machine-readable “inputs and policy versions” block:

- pinned tax table year actually used (`resolve_tax_year` result)
- pinned IRMAA table year actually used
- enabled features + configured knobs (NIIT scalars, Roth rules policy, etc.)

This can be a report appendix section so each client PDF/MD is self-contained for certification.

## 6) Handling frequent tax law changes

Some parts of tax law change often (thresholds, RMD ages, IRMAA tiers). Make this transparent by:

- Keeping values in pinned JSON with metadata (not in code)
- Tagging each release with “Tax tables updated for YYYY” in release notes
- Maintaining a small matrix in docs:
  - which years are pinned
  - which filing statuses are supported
  - which sources were used

## 7) Suggested workflow (annual)

1. Download source PDFs (IRS Rev Proc; SSA/CMS tables) and store them under `data/irs_sources/` (or similar).
2. Update the pinned JSON values and metadata.
3. Update `docs/tax/CHANGELOG.md`.
4. Run unit tests.
5. Generate a sample report and archive it (optional).

## Practical note

If you expect very frequent changes, consider:

- a small internal tool/script that imports values into JSON from a curated CSV, and
- requiring PR review that includes the source links and a screenshot/page reference (human process).
