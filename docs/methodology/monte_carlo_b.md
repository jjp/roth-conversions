# Monte Carlo (B) — correlated stock/bond simulation + charts

## Important clarification: Markov vs Monte Carlo

The current codebase **does not implement a Markov chain / regime-switching model** (no state transitions, no transition matrix). The “Monte Carlo (B)” simulation uses **i.i.d. draws** from a multivariate normal model for (stock, bond) returns plus a univariate normal model for inflation.

If you intended a _Markov regime_ model (e.g., bull/bear states with transition probabilities), that is **not currently implemented** and would need to be added explicitly.

## Implementation in this repo

Library implementation:

- `roth_conversions/simulation/monte_carlo_b.py`
  - `MonteCarloBParams`
  - `run_monte_carlo_B(inputs, strategies, params) -> pandas.DataFrame`

Notebook reference implementation (includes plots):

- `notebooks_archive/exported_cells/cell_25.py`

## Simulation model

### Randomness and reproducibility

- Random number generator: NumPy `default_rng(seed)`
- Each run is reproducible given the same `seed` and parameters.

### Stock/bond return generation (correlated normals)

For each year $t$ in a simulation path:

- Draw $z \sim \mathcal{N}(0, I)$ in $\mathbb{R}^2$
- Apply Cholesky factor $L$ of the covariance matrix $\Sigma$ so that $\varepsilon = z L^T$ has covariance $\Sigma$

Covariance matrix:

$$
\Sigma = \begin{bmatrix}
\sigma_s^2 & \rho\,\sigma_s\sigma_b \\
\rho\,\sigma_s\sigma_b & \sigma_b^2
\end{bmatrix}
$$

Then:

- $r_s = \mu_s + \varepsilon_s$
- $r_b = \mu_b + \varepsilon_b$

Returns are clamped to a safety range (defaults: -95% to +100%) to avoid extreme values destabilizing the projection.

### Inflation generation

- Inflation is modeled as i.i.d. normal: $\pi_t \sim \mathcal{N}(\mu_\pi, \sigma_\pi)$
- If `infl_mean` is not provided, it defaults to `inputs.assumptions.inflation_rate`.
- Inflation is also clamped to a safety range (defaults: -2% to +20%).

### Account-specific portfolio returns

Each account return is a weighted blend of stock and bond returns:

$$
R = w\,r_s + (1-w)\,r_b
$$

Separate stock weights are used for IRA, Roth, and taxable. Taxable additionally subtracts a simple “drag” (default 0.5%):

$$
R_{taxable} = w\,r_s + (1-w)\,r_b - drag
$$

## How simulation integrates with the deterministic tax model

For each simulation path, the Monte Carlo runner calls:

- `roth_conversions/projection.project_with_tax_tracking(...)`

passing per-year series for:

- `ira_returns`, `roth_returns`, `taxable_returns`, and `inflation_rates`.

All tax/benefit computations remain the same as in deterministic runs; only the return/inflation inputs vary.

## Output metrics

The library returns one row per (strategy, simulation):

- `after_tax`, `legacy`, `total_lifetime_tax`
- `end_total_balance`
- `min_total_balance`
- `success` where `success = (min_total_balance > 0)`

## Charts (notebook)

The notebook `cell_25.py` produces:

- Histogram overlays of `after_tax` per strategy (median shown as dashed line)
- Histogram overlays of `end_total_balance` per strategy
- Histogram of deltas in `after_tax` versus the conservative strategy

These charts are currently generated in notebooks (Matplotlib) and are not part of the CLI report output.

## Simplifying assumptions / limitations

- Returns are i.i.d. year-to-year (no serial correlation, no regime switching).
- Normal distributions can misrepresent fat tails; clamping is a pragmatic safeguard, not a statistical model.
- Taxable “drag” is a single constant; it is not derived from detailed dividend/yield/turnover modeling.

## Reviewer checklist

- Verify parameter values (`means`, `std`, correlation, stock weights, drag, clamp ranges).
- Verify reproducibility by re-running with the same `seed`.
- Verify that the deterministic tax model is called consistently for each simulated path.
