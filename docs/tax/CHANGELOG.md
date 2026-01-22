# Tax inputs changelog

This changelog tracks changes to pinned tax/benefit inputs and any related calculation logic.

## Unreleased

- Initial documentation scaffolding.

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
