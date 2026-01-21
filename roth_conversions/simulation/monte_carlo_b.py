from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

import numpy as np
import pandas as pd

from ..models import HouseholdInputs, Strategy
from ..projection import project_with_tax_tracking


@dataclass(frozen=True)
class MonteCarloBParams:
    n_sims: int = 5_000
    horizon_years: int = 25
    seed: Optional[int] = 42

    stock_mean: float = 0.08
    stock_std: float = 0.18
    bond_mean: float = 0.04
    bond_std: float = 0.07
    stock_bond_corr: float = 0.10

    infl_mean: Optional[float] = None
    infl_std: float = 0.01

    ira_stock_weight: float = 0.60
    roth_stock_weight: float = 0.80
    taxable_stock_weight: float = 0.70

    taxable_drag: float = 0.005

    asset_return_min: float = -0.95
    asset_return_max: float = 1.00
    infl_min: float = -0.02
    infl_max: float = 0.20


def _simulate_asset_paths_B(params: MonteCarloBParams):
    rng = np.random.default_rng(params.seed)

    corr = float(params.stock_bond_corr)
    corr = max(-0.99, min(0.99, corr))
    cov = np.array(
        [
            [params.stock_std**2, corr * params.stock_std * params.bond_std],
            [corr * params.stock_std * params.bond_std, params.bond_std**2],
        ],
        dtype=float,
    )
    L = np.linalg.cholesky(cov)
    z = rng.normal(size=(params.n_sims, params.horizon_years, 2))
    shocks = z @ L.T

    stock = params.stock_mean + shocks[..., 0]
    bond = params.bond_mean + shocks[..., 1]

    stock = np.clip(stock, params.asset_return_min, params.asset_return_max)
    bond = np.clip(bond, params.asset_return_min, params.asset_return_max)

    infl_mean = float(params.infl_mean) if params.infl_mean is not None else None
    if infl_mean is None:
        infl_mean = 0.0

    infl = rng.normal(loc=infl_mean, scale=params.infl_std, size=(params.n_sims, params.horizon_years))
    infl = np.clip(infl, params.infl_min, params.infl_max)

    return stock, bond, infl


def _portfolio_return(stock_r: np.ndarray, bond_r: np.ndarray, stock_wt: float) -> np.ndarray:
    w = max(0.0, min(1.0, float(stock_wt)))
    return w * stock_r + (1.0 - w) * bond_r


def run_monte_carlo_B(
    *,
    inputs: HouseholdInputs,
    strategies: Sequence[Strategy],
    params: MonteCarloBParams,
) -> pd.DataFrame:
    """Run the notebook's Monte Carlo (B) variant and return one row per sim per strategy."""

    infl_mean = float(inputs.assumptions.inflation_rate) if params.infl_mean is None else float(params.infl_mean)
    params = MonteCarloBParams(**{**params.__dict__, "infl_mean": infl_mean})

    stock, bond, infl = _simulate_asset_paths_B(params)

    rows: list[dict] = []
    for strat in strategies:
        for sim in range(params.n_sims):
            stock_r = stock[sim]
            bond_r = bond[sim]
            infl_r = infl[sim]

            ira_r = _portfolio_return(stock_r, bond_r, params.ira_stock_weight)
            roth_r = _portfolio_return(stock_r, bond_r, params.roth_stock_weight)
            taxable_r = _portfolio_return(stock_r, bond_r, params.taxable_stock_weight) - params.taxable_drag

            out = project_with_tax_tracking(
                inputs=inputs,
                strategy=strat,
                horizon_years=params.horizon_years,
                ira_returns=ira_r.tolist(),
                roth_returns=roth_r.tolist(),
                taxable_returns=taxable_r.tolist(),
                inflation_rates=infl_r.tolist(),
            )

            end_total = float(out.yearly[-1].ira_end + out.yearly[-1].roth_end + out.yearly[-1].taxable_end)
            min_total = float(
                min(y.ira_end + y.roth_end + y.taxable_end for y in out.yearly)
            )

            rows.append(
                {
                    "strategy": strat.name,
                    "sim": sim,
                    "after_tax": out.after_tax,
                    "legacy": out.legacy,
                    "total_lifetime_tax": out.total_lifetime_tax,
                    "end_total_balance": end_total,
                    "min_total_balance": min_total,
                    "success": min_total > 0.0,
                }
            )

    return pd.DataFrame(rows)
