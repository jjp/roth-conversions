# NPV and value basis (nominal vs real)

## What this covers

This document explains:

- how net present value (NPV) is computed, and
- how the report chooses nominal vs “real” (start-year dollars) values.

## Implementation in this repo

- NPV function: `roth_conversions/npv.py` (`npv(values, discount_rate)`)
- Projection uses NPV for spending/taxes: `roth_conversions/projection.py`
- Report formatting chooses basis: `roth_conversions/reporting/builder.py`

## NPV calculation

Given a series `values[t]` (year-indexed), the NPV is:

$$
NPV = \sum_{t=0}^{T-1} \frac{values[t]}{(1 + r)^t}
$$

where $r$ is the configured discount rate.

Timing convention: **year-0 timing** (the first value is undiscounted).

## Nominal vs real values in reports

The projection engine tracks an inflation multiplier per year and computes “today” values by deflating nominal values back to start-year dollars.

The report uses:

- `inputs.reporting.value_basis = "nominal"` to show nominal values, or
- `inputs.reporting.value_basis = "real"` to show start-year-dollar values.

## Simplifying assumptions / limitations

- Inflation is modeled as a constant rate in deterministic runs (or a per-year series in Monte Carlo).
- NPV is not tax-adjusted beyond the cashflows already modeled.

## Reviewer checklist

- Confirm discount rate and value basis settings.
- Confirm the timing convention aligns with your interpretation (year-0 timing).
