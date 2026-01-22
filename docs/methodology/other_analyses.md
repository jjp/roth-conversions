# Other analyses (objective selection, 32% breakeven, asset location)

## Objective selection

Implementation:

- `roth_conversions/objectives.py`

The report can choose the “best” path based on `inputs.reporting.objective`:

- `after_tax` (maximize)
- `legacy` (maximize)
- `heirs` (maximize)
- `npv_taxes` (minimize; implemented as maximizing negative PV)

If `inputs.reporting.value_basis = "real"`, objective comparisons use deflated (“today”) values when available.

## 32% question (breakeven)

Implementation:

- `roth_conversions/analysis/bracket32.py`

This analysis runs two strategies and finds the first year where:

- aggressive cumulative total tax < conservative cumulative total tax

It does not change the underlying tax model; it is a comparison of two modeled strategies.

## Asset location scenarios (Roth return sensitivity)

Implementation:

- `roth_conversions/analysis/asset_location.py`

This analysis re-runs Three Paths under alternate Roth return assumptions:

- “As configured”
- “Roth return = IRA return + Δ” for configured deltas

Important: this is a **return sensitivity** only; it does not re-allocate balances or implement full asset location optimization.

## Widow event (filing status and SS)

Implementation:

- `roth_conversions/projection.py`

Widow event behavior in the model:

- switches filing status to `Single` from the configured widow year onward
- uses the larger of the two Social Security benefits as survivor benefit
- multiplies spending need by `income_need_multiplier`

This is a planning approximation and does not model all survivor benefit details.
