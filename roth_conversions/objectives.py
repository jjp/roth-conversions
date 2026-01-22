from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

from .models import HouseholdInputs


SUPPORTED_OBJECTIVES: tuple[str, ...] = (
    "after_tax",      # maximize
    "legacy",         # maximize
    "heirs",          # maximize (if enabled)
    "npv_taxes",      # minimize (start-year dollars)
)


@dataclass(frozen=True)
class ObjectiveResult:
    objective: str
    best_label: str
    best_path_name: str


def _basis_value(*, inputs: HouseholdInputs, nominal: float, real: float) -> float:
    basis = str(inputs.reporting.value_basis)
    return float(real if basis == "real" else nominal)


def objective_value(*, inputs: HouseholdInputs, path: dict, objective: str) -> float:
    """Return a score where higher is better.

    For minimization objectives, the score is negated.
    """

    obj = str(objective)
    if obj not in SUPPORTED_OBJECTIVES:
        raise ValueError(f"unsupported objective={obj!r}; expected one of {list(SUPPORTED_OBJECTIVES)}")

    if obj == "after_tax":
        return _basis_value(
            inputs=inputs,
            nominal=float(path.get("after_tax", 0.0)),
            real=float(path.get("after_tax_today", path.get("after_tax", 0.0))),
        )

    if obj == "legacy":
        return _basis_value(
            inputs=inputs,
            nominal=float(path.get("legacy", 0.0)),
            real=float(path.get("legacy_today", path.get("legacy", 0.0))),
        )

    if obj == "heirs":
        return _basis_value(
            inputs=inputs,
            nominal=float(path.get("heirs_after_tax", 0.0)),
            real=float(path.get("heirs_after_tax_today", path.get("heirs_after_tax", 0.0))),
        )

    if obj == "npv_taxes":
        # Lower taxes is better.
        return -float(path.get("npv_taxes_today", 0.0))

    raise AssertionError("unreachable")


def pick_best_path(
    *,
    inputs: HouseholdInputs,
    labeled_paths: Iterable[Tuple[str, dict]],
) -> ObjectiveResult:
    """Pick the best path for the configured objective."""

    objective = str(getattr(inputs.reporting, "objective", "after_tax"))
    best_label, best_path = max(labeled_paths, key=lambda lp: objective_value(inputs=inputs, path=lp[1], objective=objective))
    return ObjectiveResult(objective=objective, best_label=str(best_label), best_path_name=str(best_path.get("path_name", "")))
