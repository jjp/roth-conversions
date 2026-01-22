# Medicare Part B base premium (pinned)

## What this module models

This project can optionally model the **standard Medicare Part B base premium** (monthly), as an annual household cost.

- The base premium is modeled separately from IRMAA add-ons.
- The cost is treated as an annual expense and paid from taxable assets (then IRA spillover), consistent with how IRMAA is handled.

## Sources

The model uses pinned tables in JSON:

- `roth_conversions/data/medicare/part_b_base_premium_2025.json`
  - Source: CMS fact sheet
  - https://www.cms.gov/newsroom/fact-sheets/2025-medicare-parts-b-premiums-and-deductibles
- `roth_conversions/data/medicare/part_b_base_premium_2026.json`
  - Source: SSA Medicare premiums page
  - https://www.ssa.gov/benefits/medicare/medicare-premiums.html

## Calculation (annual cost)

Let:

- $P$ = pinned Part B base premium (monthly)
- $N$ = number of covered people

Annual base premium cost is:

$$\text{PartBBaseCost} = P \times 12 \times N$$

## Simplifying assumptions / limitations

- **Enrollment timing is not modeled.** If enabled, the cost is applied each year of the projection.
- **Late enrollment penalties and special cases are not modeled.**
- **Covered people** defaults to 2 for `MFJ` and 1 otherwise, but can be overridden in config.

## Configuration

In TOML under `inputs.medicare`:

- `part_b_base_premium_enabled` (bool)
- `covered_people` (optional int)

## Where implemented

- Pinned table loader: `roth_conversions/medicare_part_b_tables.py`
- Main projection: `roth_conversions/projection.py`
- Home purchase scenario: `roth_conversions/analysis/home_purchase.py`
