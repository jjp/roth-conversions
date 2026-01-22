# Configs

## Canonical template

- `retirement_config.template.toml` is the **main** template matching the `retirement_toolkit` projection/report inputs.
- Start from this when creating a new household config.

## Example configs (ready-to-run)

- `retirement_config.minimal_roth.toml`
  - Smallest meaningful config for Roth conversion runs (has some taxable liquidity to pay conversion tax).

- `retirement_config.example.toml`
  - General-purpose example (older couple; useful for testing Social Security + near/at-RMD behavior).

- `retirement_config.scenario_couple_60_61_3m_assets_2m_ira.toml`
  - Couple ages 60/61, ~$3M total assets with ~$2M in traditional IRA.
  - Intended for Roth conversion planning in the pre-RMD years.

- `retirement_config.scenario_wife_rmd_husband_no_rmd_5m_ira.toml`
  - Wife has RMDs (age >= 73 in this model); husband does not.
  - ~$5M in traditional IRA split across spouses.

- `retirement_config.scenario_widow_event_soon.toml`
  - Widow event after a few years; switches to Single filing status and survivor SS (max of the two).

- `retirement_config.scenario_large_charity_qcd.toml`
  - Large charitable giving with QCD enabled.

## Scenario configs where Roth conversions often _don’t_ make sense

- `retirement_config.scenario_no_convert_small_ira_high_roth.toml`
  - Already Roth/taxable heavy; relatively small traditional IRA.

- `retirement_config.scenario_no_convert_roth_lower_return.toml`
  - Stress test where Roth has a lower expected return than the IRA.

- `retirement_config.scenario_no_convert_heirs_low_tax_rate.toml`
  - Heirs modeled with low effective tax rate, making “leave it in IRA” more attractive.

## Other templates

- `retirement_story_config.template.toml` / `archive/retirement_visual_config.template.toml`
  - Templates for the archived notebooks.

- `archive/roth_conversion_optimizer_config.template.toml`
  - Archived optimizer notebook template; not aligned with `retirement_toolkit` inputs.

- `frank_config.template.toml`
  - Work-in-progress forward-looking config template.

## Running

- Three Paths:
  - `python -m retirement_toolkit.cli roth --config <path> three-paths`
- Report:
  - `python -m retirement_toolkit.cli roth --config <path> report --format md --out outputs/report.md`
