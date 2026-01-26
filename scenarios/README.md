# Scenario packets (accountant review)

This repo already has runnable scenario configs under `configs/` (see `configs/README.md`).

For accountant validation, the goal is to produce a repeatable **packet per scenario** that includes:

- The exact input config used (TOML)
- A human-readable report (Markdown)
- Year-by-year CSV exports for each Path (A/B/C) so line-items (MAGI, taxes, RMDs, IRMAA, etc.) can be reviewed
- A small machine-readable `summary.json` for quick scanning / diffs

## Build packets

```pwsh
uv run python scripts/run_scenario_packets.py
```

If PDF rendering fails, install the optional dependency:

```pwsh
uv add reportlab
uv sync
```

Outputs land in:

- `outputs/scenario_packets_<timestamp>/<scenario_id>/`
  - `config.toml` (copied input)
  - `inputs_parsed.json` (normalized parsed input)
  - `report.pdf` (primary for accountant review)
  - `report.md` (optional, useful for diffing)
  - `yearly_path_a.csv`, `yearly_path_b.csv`, `yearly_path_c.csv`
  - `summary.json`
- `outputs/scenario_packets_<timestamp>/index.csv` (rollup)

A single archive is also created:

- `outputs/scenario_packets_<timestamp>.zip`

## What the accountant validates

Suggested review flow per scenario:

1. Open `config.toml` and confirm assumptions and key toggles
   - filing status, start year, discount rate
   - return assumptions + inflation
   - NIIT/state tax/IRMAA/QCD/heirs/widow switches
2. Open `report.md` for the high-level conclusions and the pinned tax-table appendix
3. Use the yearly CSVs to validate year-by-year calculations
   - total SS + RMD + conversion → MAGI
   - conversion tax + income tax (+ state/NIIT/IRMAA if enabled)
   - end balances (IRA/Roth/taxable)

Notes:

- The report is designed for **comparative planning**, not a tax-prep substitute.
- Tax tables are resolved by “latest pinned year ≤ requested year” (see `Tax Inputs & Assumptions` in the report).

## Future Teams/chat agent

For a Teams chat interface, you’ll typically want to generate a PDF in-memory and upload it.
The library now supports this via `roth_conversions.reporting.render_pdf.render_pdf_bytes(doc)`.
