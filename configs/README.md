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

## Frank scenarios (comment-driven)

These configs were added to match the items in `comments/` (see `docs/frank_scenario_crosswalk.md`).

- `retirement_config.scenario_qcd_70_5_cap_111k.toml`
  - QCD edge-case coverage with `qcd_eligible_age=70.5` and $111k cap.

- `retirement_config.scenario_ira_basis_pro_rata.toml`
  - After-tax IRA basis + pro-rata taxation.

- `retirement_config.scenario_state_tax_enabled.toml`
  - Simplified state-tax effective-rate toggle.

- `retirement_config.scenario_niit_trigger.toml`
  - NIIT stress case (large taxable investment income).

- `retirement_config.scenario_roth_5yr_penalty_home_purchase.toml`
  - Roth 5-year rule penalty exercise (via the home purchase sub-scenario in reports).

- `retirement_config.scenario_asset_location_enabled.toml`
  - Asset location sensitivity.

- `retirement_config.scenario_objective_legacy.toml`
  - Legacy objective.

- `retirement_config.scenario_objective_npv_taxes.toml`
  - NPV-of-taxes objective + discounting + longevity sensitivity.

- `retirement_config.scenario_ss_taxation_stress.toml`
  - Social Security taxation sensitivity stress case.

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
