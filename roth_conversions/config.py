from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

try:
    import tomllib  # py>=3.11
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None  # type: ignore

from .models import Household, HouseholdInputs, JointAccounts, PlanInputs, ReturnAssumptions, SpouseInputs


def _load_toml(path: Path) -> dict[str, Any]:
    if tomllib is None:
        raise RuntimeError("tomllib is not available; use Python 3.11+ or JSON configs")
    return tomllib.loads(path.read_text(encoding="utf-8"))


def load_config(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))

    if p.suffix.lower() in {".toml"}:
        return _load_toml(p)
    if p.suffix.lower() in {".json"}:
        return json.loads(p.read_text(encoding="utf-8"))

    raise ValueError(f"Unsupported config format: {p.suffix} (expected .toml or .json)")


def parse_inputs(cfg: dict[str, Any]) -> HouseholdInputs:
    """Parse the config format produced by retirement_config.template.toml."""
    inputs = cfg.get("inputs", cfg)

    household = inputs.get("household", {})
    spouse1 = inputs.get("spouse1", {})
    spouse2 = inputs.get("spouse2", {})
    joint = inputs.get("joint", {})
    plan = inputs.get("plan", {})
    assumptions = inputs.get("assumptions", {})

    return HouseholdInputs(
        household=Household(
            tax_filing_status=str(household.get("tax_filing_status", "MFJ")),
            start_year=int(household.get("start_year", 2025)),
        ),
        spouse1=SpouseInputs(
            name=str(spouse1["name"]),
            age=int(spouse1["age"]),
            traditional_ira=float(spouse1.get("traditional_ira", 0.0)),
            sep_ira=float(spouse1.get("sep_ira", 0.0)),
            roth_ira=float(spouse1.get("roth_ira", 0.0)),
            ss_start_age=int(spouse1["ss_start_age"]),
            ss_annual=float(spouse1.get("ss_annual", 0.0)),
        ),
        spouse2=SpouseInputs(
            name=str(spouse2["name"]),
            age=int(spouse2["age"]),
            traditional_ira=float(spouse2.get("traditional_ira", 0.0)),
            sep_ira=float(spouse2.get("sep_ira", 0.0)),
            roth_ira=float(spouse2.get("roth_ira", 0.0)),
            ss_start_age=int(spouse2["ss_start_age"]),
            ss_annual=float(spouse2.get("ss_annual", 0.0)),
        ),
        joint=JointAccounts(
            taxable_accounts=float(joint.get("taxable_accounts", 0.0)),
        ),
        plan=PlanInputs(
            monthly_income_need=float(plan["monthly_income_need"]),
            minimum_cash_reserve=float(plan["minimum_cash_reserve"]),
        ),
        assumptions=ReturnAssumptions(
            inflation_rate=float(assumptions["inflation_rate"]),
            taxable_return=float(assumptions["taxable_return"]),
            ira_return=float(assumptions["ira_return"]),
            roth_return=float(assumptions["roth_return"]),
        ),
    )


def load_inputs(path: str | Path) -> HouseholdInputs:
    return parse_inputs(load_config(path))


def inputs_to_dict(inputs: HouseholdInputs) -> dict[str, Any]:
    return asdict(inputs)
