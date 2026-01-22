from __future__ import annotations

from dataclasses import dataclass, replace

from ..models import HouseholdInputs, ReturnAssumptions
from .three_paths import run_three_paths
from ..objectives import pick_best_path


@dataclass(frozen=True)
class AssetLocationScenarioResult:
    name: str
    roth_return: float
    best_label: str
    best_path_name: str
    paths: object  # ThreePaths-like (dicts)


def run_asset_location_scenarios(*, inputs: HouseholdInputs, horizon_years: int = 25) -> tuple[AssetLocationScenarioResult, ...]:
    cfg = getattr(inputs, "asset_location", None)
    if not cfg or not bool(getattr(cfg, "enabled", False)):
        return ()

    deltas = tuple(float(x) for x in getattr(cfg, "roth_return_deltas", (0.0, 0.01, 0.02)))

    base = inputs.assumptions
    results: list[AssetLocationScenarioResult] = []

    # Always include the "as configured" row.
    base_paths = run_three_paths(inputs=inputs, horizon_years=horizon_years)
    base_pick = pick_best_path(inputs=inputs, labeled_paths=(("A", base_paths.path_a), ("B", base_paths.path_b), ("C", base_paths.path_c)))
    results.append(
        AssetLocationScenarioResult(
            name="As configured",
            roth_return=float(base.roth_return),
            best_label=base_pick.best_label,
            best_path_name=base_pick.best_path_name,
            paths=base_paths,
        )
    )

    for d in deltas:
        roth_r = float(base.ira_return) + float(d)
        if abs(roth_r - float(base.roth_return)) < 1e-12:
            continue

        alt_assumptions = replace(base, roth_return=roth_r)
        alt_inputs = replace(inputs, assumptions=alt_assumptions)

        paths = run_three_paths(inputs=alt_inputs, horizon_years=horizon_years)
        pick = pick_best_path(inputs=alt_inputs, labeled_paths=(("A", paths.path_a), ("B", paths.path_b), ("C", paths.path_c)))
        results.append(
            AssetLocationScenarioResult(
                name=f"Roth return = IRA return {d:+.0%}",
                roth_return=roth_r,
                best_label=pick.best_label,
                best_path_name=pick.best_path_name,
                paths=paths,
            )
        )

    return tuple(results)
