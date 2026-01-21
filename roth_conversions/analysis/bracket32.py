from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..models import HouseholdInputs, Strategy
from ..projection import project_with_tax_tracking


@dataclass(frozen=True)
class BreakevenResult:
    conservative: float
    aggressive: float
    year: Optional[int]


def find_tax_breakeven_year(
    *,
    inputs: HouseholdInputs,
    conservative: Strategy,
    aggressive: Strategy,
    horizon_years: int = 25,
) -> BreakevenResult:
    """Return first year where aggressive cumulative tax < conservative cumulative tax."""

    cons = project_with_tax_tracking(inputs=inputs, strategy=conservative, horizon_years=horizon_years)
    agg = project_with_tax_tracking(inputs=inputs, strategy=aggressive, horizon_years=horizon_years)

    breakeven: Optional[int] = None
    for yr in range(horizon_years):
        if agg.yearly[yr].cumulative_total_tax < cons.yearly[yr].cumulative_total_tax:
            breakeven = yr + 1
            break

    return BreakevenResult(conservative=cons.total_lifetime_tax, aggressive=agg.total_lifetime_tax, year=breakeven)
