"""Library-grade Roth conversion modeling tools.

This package is a refactor of the original notebook logic into:
- typed models
- pure, testable functions
- explicit data flow (no global state / no exec)
"""

from .models import (
    HouseholdInputs,
    Household,
    PlanInputs,
    ReturnAssumptions,
    SpouseInputs,
    Strategy,
)
from .projection import project_with_tax_tracking, project_path

__all__ = [
    "HouseholdInputs",
    "Household",
    "PlanInputs",
    "ReturnAssumptions",
    "SpouseInputs",
    "Strategy",
    "project_with_tax_tracking",
    "project_path",
]
