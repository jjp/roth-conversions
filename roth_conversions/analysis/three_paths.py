from __future__ import annotations

from dataclasses import dataclass

from ..models import HouseholdInputs
from ..projection import project_path


@dataclass(frozen=True)
class ThreePaths:
    path_a: dict
    path_b: dict
    path_c: dict


def run_three_paths(
    *,
    inputs: HouseholdInputs,
    path_b_annual: float = 100_000.0,
    path_b_years: int = 5,
    path_c_annual: float = 150_000.0,
    path_c_years: int = 10,
    horizon_years: int = 25,
) -> ThreePaths:
    """Notebook Chapter 3: Path A/B/C using `project_path` logic."""

    path_a = project_path(inputs=inputs, annual_conversion=0.0, conversion_years=0, path_name="Do Nothing", horizon_years=horizon_years)
    path_b = project_path(inputs=inputs, annual_conversion=path_b_annual, conversion_years=path_b_years, path_name="Smart Convert", horizon_years=horizon_years)
    path_c = project_path(inputs=inputs, annual_conversion=path_c_annual, conversion_years=path_c_years, path_name="Aggressive", horizon_years=horizon_years)

    return ThreePaths(path_a=path_a, path_b=path_b, path_c=path_c)
