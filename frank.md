# Frank Kistner comments → implementable feature list (prioritized)

Source: `comments/frank_kistner.txt`

## What Frank is asking for (in plain terms)

Frank’s note is a decision framework, not a bug list. The “features” it implies are:

- Make the tool explicit about the **objective** (income vs wealth vs heirs vs RMD minimization vs widow/IRMAA penalties).
- Model **second‑order tax effects** (Social Security taxation, IRMAA, NIIT) that are often triggered by RMDs and/or conversions.
- Respect **time value of money** (a dollar/tax paid today is not the same as a dollar/tax paid later).
- Support scenario assumptions: tax rates in future, spending paths, investment returns by account, inflation.
- Add “real life” constraints: how conversion tax is paid, QCDs, life expectancy uncertainty, heirs’ tax rates, Roth 5‑year rules, and asset location/risk choices.

## What the current code already does (and what it simplifies)

**Already supported (basic):**

- Inputs: ages, SS start/annual, IRA/Roth balances, taxable balance, inflation + returns by account via config.
  - See `configs/retirement_config.template.toml` and parsing in `roth_conversions/config.py`.
- Projection engine: annual loop with RMDs, withdrawals, conversions, simple tax tracking.
  - See `roth_conversions/projection.py`.
- Reporting: basic “after‑tax wealth” + “legacy” comparisons.
  - See `roth_conversions/reporting/builder.py`.

**Major simplifications/gaps (important context for implementation):**

- Taxes are still simplified (ordinary income only), but now use **pinned IRS-sourced tables** by tax year and filing status (`MFJ` + `Single`).
  - Pinned JSON: `roth_conversions/data/tax/us_federal_ordinary_income_2024.json`, `..._2025.json`, `..._2026.json`
  - Loader: `roth_conversions/tax_tables.py`
- Social Security taxable benefits now use the **provisional income** method (instead of “always 85% taxable”).
  - See `roth_conversions/social_security.py` and usage in `roth_conversions/projection.py`.
- No IRMAA, no NIIT, no widow/widower filing-status change, no QCD handling.
- “After-tax wealth” / “legacy” are heuristics (e.g., `ira * 0.75`, `taxable * 0.92`, `ira * (1-0.28)`), not a modeled tax event.
- Time value of money is not modeled (no discounting / NPV objective).

---

## Feature list + importance (do these in order)

### P0 — Foundation (high importance; unblock everything else)

1. **Generalize the tax engine beyond MFJ 2024** ✅ Done

- **Why**: Almost every Frank objective depends on accurate marginal/average taxes under different conditions.
- **Scope**:
  - Add filing statuses at least: `MFJ`, `Single`.
  - Allow selecting tax year/bracket set and standard deduction by status.
  - Optionally index thresholds via inflation.
- **Likely files**:
  - `roth_conversions/tax.py` (new bracket tables + API)
  - `roth_conversions/projection.py` (stop assuming MFJ only)
  - `roth_conversions/models.py` + `roth_conversions/config.py` (config options)
- **Acceptance**:
  - Can compute tax for MFJ vs Single.
  - Can run the same scenario with a “widow year” status change later (even if widow logic comes in P1).

2. **Implement real Social Security taxation (provisional income method)** ✅ Done

- **Why**: Frank explicitly calls out “up to 85% taxable” as a triggered effect; current model overstates taxable SS for many cases.
- **Scope**:
  - Compute taxable SS using IRS rules (base + adjusted base thresholds depend on filing status).
  - Feed taxable SS into taxable income / MAGI.
- **Likely files**:
  - Add `roth_conversions/ss_tax.py` or extend `roth_conversions/tax.py`
  - Update `roth_conversions/projection.py`
- **Acceptance**:
  - Unit tests for a few representative cases (low provisional income → 0% taxable; mid; high → ~85%).

3. **Make objectives explicit and report them**

- **Why**: Frank’s first section is “what is my end objective?” and the tool should reflect that.
- **Scope**:
  - Add config `objective` with options like:
    - `maximize_after_tax_wealth` (current default)
    - `maximize_after_tax_income_npv` (new)
    - `maximize_legacy` (heirs)
    - `minimize_rmd` (proxy metric)
    - `minimize_total_tax` (already tracked)
  - Report a table of all objective metrics for each strategy.
- **Likely files**:
  - `roth_conversions/models.py` (enum/strings)
  - `roth_conversions/projection.py` (compute additional metrics)
  - `roth_conversions/reporting/builder.py`
- **Acceptance**:
  - CLI report shows objective metrics side-by-side for A/B/C (and 32% comparison).

### P1 — High-impact realism (still high importance)

4. **Model Medicare IRMAA as an explicit cost**

- **Why**: Frank calls this out as a key Roth conversion risk; conversions can spike MAGI and trigger IRMAA tiers.
- **Scope**:
  - Compute MAGI each year (start with AGI proxy + add-back rules as needed).
  - Apply IRMAA tiers (MFJ vs Single thresholds), convert to annual premium surcharge cost.
  - Subtract IRMAA cost from taxable or from “after-tax spending capacity.”
- **Likely files**:
  - New module: `roth_conversions/irmaa.py`
  - `roth_conversions/projection.py`
  - Config template additions.
- **Acceptance**:
  - A scenario with high conversions shows higher IRMAA costs than no-conversion.

5. **Model NIIT (Net Investment Income Tax) where applicable**

- **Why**: Frank lists NIIT thresholds; important for higher-income households and high taxable returns.
- **Scope**:
  - Track net investment income (at minimum: taxable account growth/withdrawals; optionally dividends/cap gains approximations).
  - Apply NIIT on lesser of NII and excess MAGI over threshold.
- **Likely files**:
  - New module: `roth_conversions/niit.py` or in `tax.py`
  - `roth_conversions/projection.py`
- **Acceptance**:
  - High-income scenario triggers NIIT; low-income does not.

6. **Widow/Widower penalty: filing status transition + threshold changes**

- **Why**: Frank highlights this explicitly; it’s a core motivator for “pre-paying” tax via conversions.
- **Scope**:
  - Add config for an assumed first-death year (or ages) and survivor.
  - From that year forward, set filing status to `Single`.
  - Optionally reduce household income need (one-person household) and adjust SS benefits (survivor keeps higher benefit).
- **Likely files**:
  - `roth_conversions/models.py` + `roth_conversions/config.py` (new inputs)
  - `roth_conversions/projection.py`
- **Acceptance**:
  - A/B/C results change meaningfully when widow event is enabled.

7. **How conversion tax is paid (taxable vs IRA)** ✅ Done

- **Why**: Frank lists this and the opportunity cost; current model assumes taxes effectively come from taxable (and also subtracts 50% of income tax from taxable as a rough approximation).
- **Scope**:
  - Add config: `inputs.withdrawal_policy.income_tax_payment_source = "taxable"|"ira"`.
  - Add config: `inputs.withdrawal_policy.conversion_tax_payment_source = "taxable"|"ira"`.
  - If paid from IRA, reduce IRA using a marginal-rate gross-up approximation (withholding model).
  - Replace the heuristic `taxable -= income_tax * 0.5` with the explicit policy.
- **Likely files**:
  - `roth_conversions/projection.py`
  - Config template.
- **Acceptance**:
  - Same conversion strategy produces different outcomes depending on payment source.

### P2 — Decision-quality improvements (medium importance)

8. **Time value of money: NPV (discounted) objectives**

- **Why**: Frank calls out that most tools ignore this.
- **Scope**:
  - Add config: `discount_rate`.
  - Compute NPV of after-tax spending and/or NPV of taxes paid.
  - Use NPV in objective comparisons.
- **Likely files**:
  - `roth_conversions/projection.py` (track annual net cash flow)
  - Reporting.
- **Acceptance**:
  - `maximize_after_tax_income_npv` prefers earlier cash flows when discount_rate > 0.

9. **QCD support (age 70½+)**

- **Why**: Frank’s guidance: don’t convert dollars you’ll later QCD.
- **Scope**:
  - Add config: planned annual QCD amount (and start age/year).
  - Reduce taxable income while still satisfying part of RMD.
- **Likely files**:
  - `roth_conversions/projection.py`
  - Config template.
- **Acceptance**:
  - With QCD enabled, taxable income and taxes drop vs baseline at same RMD.

10. **Life expectancy / longevity sensitivity**

- **Why**: Frank emphasizes “Roth conversions pay off the longer you live.”
- **Scope options**:
  - Simple: allow multiple horizons (e.g., 10/20/30 years) and show a sensitivity table.
  - Better: add mortality curve and compute expected value of outcomes.
- **Likely files**:
  - `roth_conversions/projection.py` (scenario runner)
  - Reporting.
- **Acceptance**:
  - Report includes a “Longevity sensitivity” section.

### P3 — Advanced / nice-to-have (lower importance unless your use-case demands it)

11. **Heirs’ tax modeling (10‑year inherited IRA rule, heirs’ bracket)**

- **Why**: Frank asks about heirs in equal/higher brackets.
- **Scope**:
  - Add config: `heir_effective_tax_rate` (simple) OR a distribution schedule over 10 years.
  - Replace current `legacy` heuristic with a modeled “after-tax to heirs.”
- **Likely files**:
  - `roth_conversions/projection.py` (end-of-horizon estate event)
  - Reporting.

12. **Roth 5-year rule tracking**

- **Why**: Mentioned explicitly; typically matters if you need to withdraw conversion principal soon.
- **Scope**:
  - Track conversions by year and prevent Roth withdrawals from recently converted principal if within 5 years (or apply penalty model).
- **Likely files**:
  - `roth_conversions/projection.py`

13. **Asset location / risk: put higher-growth assets in Roth**

- **Why**: Frank’s item #16.
- **Reality check**:
  - You _already_ support different return assumptions by account (`ira_return`, `roth_return`, `taxable_return`).
  - The missing piece is making this a first-class scenario knob and explaining it in reports.
- **Possible scope**:
  - Add config presets or scenario runner that compares `roth_return = ira_return` vs `roth_return > ira_return`.

---

## Suggested implementation order (fastest path to value)

1. P0.1 tax engine generalization
2. P0.2 SS taxation formula
3. P1.7 explicit tax payment source (remove heuristics) ✅ Done
4. P1.4 IRMAA ✅ Done (basic: pinned tiers + 2-year lookback)
5. P1.6 widow penalty
6. P2.8 NPV/time value of money
7. P2.9 QCD
8. P3 heirs + 5-year rules as needed

## Notes on config additions (where to extend)

- Start in `configs/retirement_config.template.toml` and update parsing in `roth_conversions/config.py`.
- Keep defaults identical to today so existing CLI runs don’t break.

## Testing recommendations

- Add targeted unit tests in `tests/` for:
  - SS taxable calculation
  - IRMAA tier calculation
  - Filing status tax differences
  - Widow year transition behavior
