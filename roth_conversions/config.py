from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

try:
    import tomllib  # py>=3.11
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None  # type: ignore

from .models import (
    AssetLocationInputs,
    CharitableGivingInputs,
    Household,
    HouseholdInputs,
    HeirsInputs,
    JointAccounts,
    MedicareInputs,
    NIITInputs,
    ItemizedDeductionsInputs,
    PlanInputs,
    PreferentialIncomeInputs,
    ReportingInputs,
    RothRulesInputs,
    ReturnAssumptions,
    StateTaxInputs,
    SpouseInputs,
    TaxPaymentPolicy,
    WidowEventInputs,
)


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

    reporting = inputs.get("reporting", {})
    reporting_inputs = ReportingInputs(
        value_basis=str(reporting.get("value_basis", "nominal")),
        objective=str(reporting.get("objective", "after_tax")),
        longevity_sensitivity_enabled=bool(reporting.get("longevity_sensitivity_enabled", False)),
        longevity_horizons_years=tuple(int(x) for x in reporting.get("longevity_horizons_years", (20, 25, 30, 35))),
    )
    if reporting_inputs.value_basis not in {"nominal", "real"}:
        raise ValueError(
            f"invalid inputs.reporting.value_basis={reporting_inputs.value_basis!r}; expected 'nominal' or 'real'"
        )
    if reporting_inputs.objective not in {"after_tax", "legacy", "heirs", "npv_taxes"}:
        raise ValueError(
            f"invalid inputs.reporting.objective={reporting_inputs.objective!r}; expected 'after_tax', 'legacy', 'heirs', or 'npv_taxes'"
        )
    if any(int(x) <= 0 for x in reporting_inputs.longevity_horizons_years):
        raise ValueError("inputs.reporting.longevity_horizons_years must contain only positive integers")

    events = inputs.get("events", {})
    widow_event_enabled = bool(events.get("widow_event_enabled", False))
    widow_year_raw = events.get("widow_year")
    widow_year = int(widow_year_raw) if widow_year_raw is not None else None
    survivor = str(events.get("survivor", "spouse1"))
    income_need_multiplier = float(events.get("income_need_multiplier", 1.0))
    if survivor not in {"spouse1", "spouse2"}:
        raise ValueError(f"invalid inputs.events.survivor={survivor!r}; expected 'spouse1' or 'spouse2'")
    if income_need_multiplier <= 0:
        raise ValueError(
            f"invalid inputs.events.income_need_multiplier={income_need_multiplier!r}; expected > 0"
        )
    if widow_event_enabled and widow_year is None:
        raise ValueError("inputs.events.widow_year is required when widow_event_enabled=true")
    widow_event = WidowEventInputs(
        enabled=widow_event_enabled,
        widow_year=widow_year,
        survivor=survivor,
        income_need_multiplier=income_need_multiplier,
    )

    medicare = inputs.get("medicare", {})
    medicare_inputs = MedicareInputs(
        irmaa_enabled=bool(medicare.get("irmaa_enabled", False)),
        part_b_base_premium_enabled=bool(medicare.get("part_b_base_premium_enabled", False)),
        covered_people=(int(medicare["covered_people"]) if medicare.get("covered_people") is not None else None),
    )
    if medicare_inputs.covered_people is not None and int(medicare_inputs.covered_people) <= 0:
        raise ValueError("inputs.medicare.covered_people must be a positive integer when provided")

    taxes = inputs.get("taxes", {})
    niit_inputs = NIITInputs(
        enabled=bool(taxes.get("niit_enabled", False)),
        nii_fraction_of_return=float(taxes.get("niit_nii_fraction_of_return", 0.70)),
        realization_fraction=float(taxes.get("niit_realization_fraction", 0.60)),
    )
    if not (0.0 <= float(niit_inputs.nii_fraction_of_return) <= 1.0):
        raise ValueError("inputs.taxes.niit_nii_fraction_of_return must be between 0 and 1")
    if not (0.0 <= float(niit_inputs.realization_fraction) <= 1.0):
        raise ValueError("inputs.taxes.niit_realization_fraction must be between 0 and 1")

    state_tax_inputs = StateTaxInputs(
        enabled=bool(taxes.get("state_tax_enabled", False)),
        rate=float(taxes.get("state_tax_rate", 0.0)),
        base=str(taxes.get("state_tax_base", "agi")),
    )
    if not (0.0 <= float(state_tax_inputs.rate) <= 1.0):
        raise ValueError("inputs.taxes.state_tax_rate must be between 0 and 1")
    if state_tax_inputs.base not in {"agi", "taxable_income"}:
        raise ValueError("inputs.taxes.state_tax_base must be 'agi' or 'taxable_income'")

    preferential_income_inputs = PreferentialIncomeInputs(
        qualified_dividends_annual=float(taxes.get("qualified_dividends_annual", 0.0)),
        long_term_capital_gains_annual=float(taxes.get("long_term_capital_gains_annual", 0.0)),
    )
    if preferential_income_inputs.qualified_dividends_annual < 0:
        raise ValueError("inputs.taxes.qualified_dividends_annual must be >= 0")
    if preferential_income_inputs.long_term_capital_gains_annual < 0:
        raise ValueError("inputs.taxes.long_term_capital_gains_annual must be >= 0")

    itemized_deductions_inputs = ItemizedDeductionsInputs(
        enabled=bool(taxes.get("itemized_deductions_enabled", False)),
        itemized_deductions_annual=float(taxes.get("itemized_deductions_annual", 0.0)),
    )
    if itemized_deductions_inputs.itemized_deductions_annual < 0:
        raise ValueError("inputs.taxes.itemized_deductions_annual must be >= 0")

    roth_rules = inputs.get("roth_rules", {})
    roth_rules_inputs = RothRulesInputs(
        enabled=bool(roth_rules.get("enabled", False)),
        conversion_wait_years=int(roth_rules.get("conversion_wait_years", 5)),
        qualified_age_years=int(roth_rules.get("qualified_age_years", 60)),
        penalty_rate=float(roth_rules.get("penalty_rate", 0.10)),
        policy=str(roth_rules.get("policy", "penalty")),
    )
    if roth_rules_inputs.conversion_wait_years <= 0:
        raise ValueError("inputs.roth_rules.conversion_wait_years must be > 0")
    if roth_rules_inputs.qualified_age_years <= 0:
        raise ValueError("inputs.roth_rules.qualified_age_years must be > 0")
    if not (0.0 <= float(roth_rules_inputs.penalty_rate) <= 1.0):
        raise ValueError("inputs.roth_rules.penalty_rate must be between 0 and 1")
    if roth_rules_inputs.policy not in {"penalty", "prevent"}:
        raise ValueError("inputs.roth_rules.policy must be 'penalty' or 'prevent'")

    asset_location = inputs.get("asset_location", {})
    deltas_raw = asset_location.get("roth_return_deltas", (0.0, 0.01, 0.02))
    deltas: tuple[float, ...]
    if isinstance(deltas_raw, (list, tuple)):
        deltas = tuple(float(x) for x in deltas_raw)
    else:
        deltas = (0.0, 0.01, 0.02)
    asset_location_inputs = AssetLocationInputs(
        enabled=bool(asset_location.get("enabled", False)),
        roth_return_deltas=deltas,
    )

    withdrawal_policy = inputs.get("withdrawal_policy", {})
    tax_payment_policy = TaxPaymentPolicy(
        income_tax_payment_source=str(withdrawal_policy.get("income_tax_payment_source", "taxable")),
        conversion_tax_payment_source=str(withdrawal_policy.get("conversion_tax_payment_source", "taxable")),
    )

    allowed_sources = {"taxable", "ira"}
    if tax_payment_policy.income_tax_payment_source not in allowed_sources:
        raise ValueError(
            f"invalid inputs.withdrawal_policy.income_tax_payment_source={tax_payment_policy.income_tax_payment_source!r}; "
            f"expected one of {sorted(allowed_sources)}"
        )
    if tax_payment_policy.conversion_tax_payment_source not in allowed_sources:
        raise ValueError(
            f"invalid inputs.withdrawal_policy.conversion_tax_payment_source={tax_payment_policy.conversion_tax_payment_source!r}; "
            f"expected one of {sorted(allowed_sources)}"
        )

    charity = inputs.get("charity", {})
    charity_inputs = CharitableGivingInputs(
        enabled=bool(charity.get("enabled", False)),
        annual_amount=float(charity.get("annual_amount", 0.0)),
        use_qcd=bool(charity.get("use_qcd", True)),
        qcd_eligible_age=float(charity.get("qcd_eligible_age", 70.5)),
        qcd_annual_cap_per_person=float(charity.get("qcd_annual_cap_per_person", 111_000.0)),
    )
    if charity_inputs.annual_amount < 0:
        raise ValueError("inputs.charity.annual_amount must be >= 0")
    if float(charity_inputs.qcd_eligible_age) < 0:
        raise ValueError("inputs.charity.qcd_eligible_age must be >= 0")
    if charity_inputs.qcd_annual_cap_per_person < 0:
        raise ValueError("inputs.charity.qcd_annual_cap_per_person must be >= 0")

    heirs = inputs.get("heirs", {})
    heirs_inputs = HeirsInputs(
        enabled=bool(heirs.get("enabled", False)),
        distribution_years=int(heirs.get("distribution_years", 10)),
        heir_tax_rate=float(heirs.get("heir_tax_rate", 0.30)),
    )
    if heirs_inputs.distribution_years <= 0:
        raise ValueError("inputs.heirs.distribution_years must be > 0")
    if not (0.0 <= heirs_inputs.heir_tax_rate <= 1.0):
        raise ValueError("inputs.heirs.heir_tax_rate must be between 0 and 1")

    return HouseholdInputs(
        household=Household(
            tax_filing_status=str(household.get("tax_filing_status", "MFJ")),
            start_year=int(household.get("start_year", 2025)),
            discount_rate=float(household.get("discount_rate", 0.0)),
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
            ira_after_tax_basis=float(joint.get("ira_after_tax_basis", 0.0)),
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
        tax_payment_policy=tax_payment_policy,
        medicare=medicare_inputs,
        state_tax=state_tax_inputs,
        widow_event=widow_event,
        reporting=reporting_inputs,
        niit=niit_inputs,
        preferential_income=preferential_income_inputs,
        itemized_deductions=itemized_deductions_inputs,
        roth_rules=roth_rules_inputs,
        asset_location=asset_location_inputs,
        charity=charity_inputs,
        heirs=heirs_inputs,
    )


def load_inputs(path: str | Path) -> HouseholdInputs:
    return parse_inputs(load_config(path))


def inputs_to_dict(inputs: HouseholdInputs) -> dict[str, Any]:
    return asdict(inputs)
