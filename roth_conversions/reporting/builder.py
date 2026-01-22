from __future__ import annotations

from datetime import datetime

import re
from typing import Iterable, Sequence

from ..analysis.bracket32 import find_tax_breakeven_year
from ..analysis.asset_location import run_asset_location_scenarios
from ..analysis.home_purchase import project_with_home_purchase
from ..analysis.three_paths import run_three_paths
from ..models import HouseholdInputs, Strategy
from ..objectives import pick_best_path
from ..projection import project_with_tax_tracking
from .. import tax_tables
from .. import irmaa_tables
from .models import ReportDocument, ReportSection, ReportTable


def _money(x: float) -> str:
    return f"${x:,.0f}"


def _basis_money(*, inputs: HouseholdInputs, nominal: float, real: float) -> str:
    basis = str(inputs.reporting.value_basis)
    return _money(real if basis == "real" else nominal)


def _section_key(title: str) -> str:
    """Stable-ish key for CLI include/exclude.

    Note: this is intentionally simple; keys are derived from titles.
    """

    cleaned = re.sub(r"[^a-z0-9]+", "-", title.lower())
    return cleaned.strip("-")


def list_default_report_sections() -> tuple[tuple[str, str], ...]:
    titles = (
        "Executive Summary",
        "Three Paths (A/B/C)",
        "Objective Summary",
        "Asset Location Scenarios",
        "Longevity Sensitivity",
        "32% Question (Breakeven)",
        "Home Purchase Scenario",
        "Tax Inputs & Assumptions",
    )
    return tuple((_section_key(t), t) for t in titles)


def _flatten_csv(values: Sequence[str] | None) -> tuple[str, ...]:
    if not values:
        return ()
    out: list[str] = []
    for v in values:
        for part in str(v).split(","):
            p = part.strip()
            if p:
                out.append(p)
    return tuple(out)


def _filter_sections(
    sections: Sequence[ReportSection],
    *,
    include_sections: Sequence[str] | None,
    exclude_sections: Sequence[str] | None,
) -> tuple[ReportSection, ...]:
    includes = {_section_key(x) for x in _flatten_csv(include_sections)}
    excludes = {_section_key(x) for x in _flatten_csv(exclude_sections)}

    filtered: Iterable[ReportSection] = sections
    if includes:
        filtered = (s for s in filtered if _section_key(s.title) in includes)
    if excludes:
        filtered = (s for s in filtered if _section_key(s.title) not in excludes)
    return tuple(filtered)


def build_report(
    *,
    inputs: HouseholdInputs,
    home_down_payment: float = 200_000.0,
    home_purchase_year: int = 2027,
    include_sections: Sequence[str] | None = None,
    exclude_sections: Sequence[str] | None = None,
) -> ReportDocument:
    """Build a minimal report for emailing.

    Current scope: derived from the new library analyses (notebook Chapters 3, 8, 9).
    """

    created_at = datetime.now()
    household_name = f"{inputs.spouse1.name} + {inputs.spouse2.name}"
    title = f"Roth Conversion Report — {household_name}"

    # Compute the key analytics first so we can build an executive summary.
    paths = run_three_paths(inputs=inputs)
    conservative = Strategy("Conservative (100K x 5, ≤24%)", 100_000, 5, allow_32_bracket=False)
    aggressive = Strategy("Aggressive (175K x 8, allow 32%)", 175_000, 8, allow_32_bracket=True)
    breakeven = find_tax_breakeven_year(inputs=inputs, conservative=conservative, aggressive=aggressive)

    home = project_with_home_purchase(
        inputs=inputs,
        purchase_year=int(home_purchase_year),
        down_payment=float(home_down_payment),
    )

    sections: list[ReportSection] = []

    # --- Executive summary ---
    path_rows = [
        ("A", paths.path_a),
        ("B", paths.path_b),
        ("C", paths.path_c),
    ]
    objective_pick = pick_best_path(inputs=inputs, labeled_paths=path_rows)
    best_label, best_path = next((lbl, p) for (lbl, p) in path_rows if lbl == objective_pick.best_label)

    # One representative run to surface PV metrics (strategy doesn't matter for spend PV; taxes do).
    # We use a conservative strategy to keep the values stable.
    pv_result = project_with_tax_tracking(
        inputs=inputs,
        strategy=Strategy("PV", annual_conversion=0.0, conversion_years=0, allow_32_bracket=False),
        horizon_years=25,
    )
    widow_line = (
        f"- Widow event: enabled (widow_year={inputs.widow_event.widow_year}, income_need_multiplier={inputs.widow_event.income_need_multiplier:g})"
        if bool(inputs.widow_event.enabled)
        else "- Widow event: disabled"
    )
    irmaa_line = "- IRMAA: enabled (2-year lookback MAGI approximation)" if bool(inputs.medicare.irmaa_enabled) else "- IRMAA: disabled"
    charity_line = (
        f"- Charity/QCD: enabled (annual_amount={_money(float(inputs.charity.annual_amount))}, use_qcd={bool(inputs.charity.use_qcd)}, qcd_eligible_age={int(inputs.charity.qcd_eligible_age)})"
        if bool(inputs.charity.enabled)
        else "- Charity/QCD: disabled"
    )
    heirs_line = (
        f"- Heirs: enabled (distribution_years={int(inputs.heirs.distribution_years)}, heir_tax_rate={float(inputs.heirs.heir_tax_rate):g})"
        if bool(inputs.heirs.enabled)
        else "- Heirs: disabled"
    )
    niit_line = (
        f"- NIIT: enabled (realized NII ≈ taxable_return × {float(inputs.niit.nii_fraction_of_return):g} × {float(inputs.niit.realization_fraction):g})"
        if bool(inputs.niit.enabled)
        else "- NIIT: disabled"
    )

    roth_rules_line = (
        f"- Roth 5-year rule (conversions): enabled (policy={inputs.roth_rules.policy}, wait_years={int(inputs.roth_rules.conversion_wait_years)}, qualified_age≈{int(inputs.roth_rules.qualified_age_years)})"
        if bool(inputs.roth_rules.enabled)
        else "- Roth 5-year rule (conversions): disabled"
    )

    summary_lines = [
        f"- Objective: {objective_pick.objective} (basis={inputs.reporting.value_basis})",
        f"- Best by objective: Path {best_label} ({best_path['path_name']})",
        f"- Best after-tax wealth: Path {max(path_rows, key=lambda r: float(r[1]['after_tax']))[0]} at {_basis_money(inputs=inputs, nominal=float(max(path_rows, key=lambda r: float(r[1]['after_tax']))[1]['after_tax']), real=float(max(path_rows, key=lambda r: float(r[1]['after_tax']))[1].get('after_tax_today', max(path_rows, key=lambda r: float(r[1]['after_tax']))[1]['after_tax'])))}",
        f"- B − A (after-tax): {_basis_money(inputs=inputs, nominal=paths.path_b['after_tax'] - paths.path_a['after_tax'], real=float(paths.path_b.get('after_tax_today', paths.path_b['after_tax']) - float(paths.path_a.get('after_tax_today', paths.path_a['after_tax']))))}",
        f"- C − A (after-tax): {_basis_money(inputs=inputs, nominal=paths.path_c['after_tax'] - paths.path_a['after_tax'], real=float(paths.path_c.get('after_tax_today', paths.path_c['after_tax']) - float(paths.path_a.get('after_tax_today', paths.path_a['after_tax']))))}",
        widow_line,
        irmaa_line,
        niit_line,
        roth_rules_line,
        charity_line,
        heirs_line,
        f"- PV of spending (start-year $): {_money(float(pv_result.npv_spending_today))} (discount_rate={float(inputs.household.discount_rate):g})",
        f"- PV of taxes (start-year $): {_money(float(pv_result.npv_taxes_today))}",
        "- 32% breakeven: "
        + (f"Year {breakeven.year}" if breakeven.year is not None else "Not reached"),
        f"- Home purchase scenario: after-tax {_basis_money(inputs=inputs, nominal=home.after_tax, real=home.after_tax / ((home.yearly_data[-1].get('inflation_multiplier', 1.0)) if home.yearly_data else 1.0))}, legacy {_basis_money(inputs=inputs, nominal=home.legacy, real=home.legacy / ((home.yearly_data[-1].get('inflation_multiplier', 1.0)) if home.yearly_data else 1.0))}",
    ]
    sections.append(
        ReportSection(
            title="Executive Summary",
            paragraphs=(
                "Key takeaways:",
                "\n".join(summary_lines),
            ),
        )
    )

    # --- Three paths ---
    sections.append(
        ReportSection(
            title="Three Paths (A/B/C)",
            paragraphs=(
                "Compares three conversion strategies using the year-by-year projection model.",
            ),
            tables=(
                ReportTable(
                    headers=["Path", "Strategy", "After-tax wealth", "Legacy", "Heirs (after-tax)", "First RMD", "IRMAA total", "NIIT total", "Roth penalty total", "PV taxes (start-year $)"],
                    rows=(
                        (
                            "A",
                            paths.path_a["path_name"],
                            _basis_money(inputs=inputs, nominal=float(paths.path_a["after_tax"]), real=float(paths.path_a.get("after_tax_today", paths.path_a["after_tax"]))),
                            _basis_money(inputs=inputs, nominal=float(paths.path_a["legacy"]), real=float(paths.path_a.get("legacy_today", paths.path_a["legacy"]))),
                            _basis_money(inputs=inputs, nominal=float(paths.path_a.get("heirs_after_tax", 0.0)), real=float(paths.path_a.get("heirs_after_tax_today", paths.path_a.get("heirs_after_tax", 0.0)))),
                            _money(paths.path_a["first_rmd"]),
                            _money(float(paths.path_a.get("total_irmaa_cost", 0.0))),
                            _money(float(paths.path_a.get("total_niit_tax", 0.0))),
                            _money(float(paths.path_a.get("total_roth_penalty_tax", 0.0))),
                            _money(float(paths.path_a.get("npv_taxes_today", 0.0))),
                        ),
                        (
                            "B",
                            paths.path_b["path_name"],
                            _basis_money(inputs=inputs, nominal=float(paths.path_b["after_tax"]), real=float(paths.path_b.get("after_tax_today", paths.path_b["after_tax"]))),
                            _basis_money(inputs=inputs, nominal=float(paths.path_b["legacy"]), real=float(paths.path_b.get("legacy_today", paths.path_b["legacy"]))),
                            _basis_money(inputs=inputs, nominal=float(paths.path_b.get("heirs_after_tax", 0.0)), real=float(paths.path_b.get("heirs_after_tax_today", paths.path_b.get("heirs_after_tax", 0.0)))),
                            _money(paths.path_b["first_rmd"]),
                            _money(float(paths.path_b.get("total_irmaa_cost", 0.0))),
                            _money(float(paths.path_b.get("total_niit_tax", 0.0))),
                            _money(float(paths.path_b.get("total_roth_penalty_tax", 0.0))),
                            _money(float(paths.path_b.get("npv_taxes_today", 0.0))),
                        ),
                        (
                            "C",
                            paths.path_c["path_name"],
                            _basis_money(inputs=inputs, nominal=float(paths.path_c["after_tax"]), real=float(paths.path_c.get("after_tax_today", paths.path_c["after_tax"]))),
                            _basis_money(inputs=inputs, nominal=float(paths.path_c["legacy"]), real=float(paths.path_c.get("legacy_today", paths.path_c["legacy"]))),
                            _basis_money(inputs=inputs, nominal=float(paths.path_c.get("heirs_after_tax", 0.0)), real=float(paths.path_c.get("heirs_after_tax_today", paths.path_c.get("heirs_after_tax", 0.0)))),
                            _money(paths.path_c["first_rmd"]),
                            _money(float(paths.path_c.get("total_irmaa_cost", 0.0))),
                            _money(float(paths.path_c.get("total_niit_tax", 0.0))),
                            _money(float(paths.path_c.get("total_roth_penalty_tax", 0.0))),
                            _money(float(paths.path_c.get("npv_taxes_today", 0.0))),
                        ),
                    ),
                ),
                ReportTable(
                    headers=["Delta", "Value"],
                    rows=(
                        (
                            "B − A (after-tax)",
                            _basis_money(
                                inputs=inputs,
                                nominal=float(paths.path_b["after_tax"] - paths.path_a["after_tax"]),
                                real=float(paths.path_b.get("after_tax_today", paths.path_b["after_tax"]) - float(paths.path_a.get("after_tax_today", paths.path_a["after_tax"]))),
                            ),
                        ),
                        (
                            "B − A (legacy)",
                            _basis_money(
                                inputs=inputs,
                                nominal=float(paths.path_b["legacy"] - paths.path_a["legacy"]),
                                real=float(paths.path_b.get("legacy_today", paths.path_b["legacy"]) - float(paths.path_a.get("legacy_today", paths.path_a["legacy"]))),
                            ),
                        ),
                        (
                            "B − A (heirs)",
                            _basis_money(
                                inputs=inputs,
                                nominal=float(paths.path_b.get("heirs_after_tax", 0.0) - float(paths.path_a.get("heirs_after_tax", 0.0))),
                                real=float(paths.path_b.get("heirs_after_tax_today", paths.path_b.get("heirs_after_tax", 0.0)) - float(paths.path_a.get("heirs_after_tax_today", paths.path_a.get("heirs_after_tax", 0.0)))),
                            ),
                        ),
                        (
                            "C − A (after-tax)",
                            _basis_money(
                                inputs=inputs,
                                nominal=float(paths.path_c["after_tax"] - paths.path_a["after_tax"]),
                                real=float(paths.path_c.get("after_tax_today", paths.path_c["after_tax"]) - float(paths.path_a.get("after_tax_today", paths.path_a["after_tax"]))),
                            ),
                        ),
                        (
                            "C − A (legacy)",
                            _basis_money(
                                inputs=inputs,
                                nominal=float(paths.path_c["legacy"] - paths.path_a["legacy"]),
                                real=float(paths.path_c.get("legacy_today", paths.path_c["legacy"]) - float(paths.path_a.get("legacy_today", paths.path_a["legacy"]))),
                            ),
                        ),
                        (
                            "C − A (heirs)",
                            _basis_money(
                                inputs=inputs,
                                nominal=float(paths.path_c.get("heirs_after_tax", 0.0) - float(paths.path_a.get("heirs_after_tax", 0.0))),
                                real=float(paths.path_c.get("heirs_after_tax_today", paths.path_c.get("heirs_after_tax", 0.0)) - float(paths.path_a.get("heirs_after_tax_today", paths.path_a.get("heirs_after_tax", 0.0)))),
                            ),
                        ),
                    ),
                ),
            ),
        )
    )

    # --- Asset location scenarios ---
    asset_location_results = run_asset_location_scenarios(inputs=inputs, horizon_years=25)
    if asset_location_results:
        rows: list[tuple[str, ...]] = []
        for res in asset_location_results:
            # res.paths is a ThreePaths
            path_rows2 = [("A", res.paths.path_a), ("B", res.paths.path_b), ("C", res.paths.path_c)]
            pick = pick_best_path(inputs=inputs, labeled_paths=path_rows2)
            best_lbl, best_p = next((lbl, p) for (lbl, p) in path_rows2 if lbl == pick.best_label)
            rows.append(
                (
                    res.name,
                    f"{float(res.roth_return):.2%}",
                    f"{best_lbl} ({best_p['path_name']})",
                    _basis_money(inputs=inputs, nominal=float(best_p["after_tax"]), real=float(best_p.get("after_tax_today", best_p["after_tax"]))),
                    _money(float(best_p.get("npv_taxes_today", 0.0))),
                )
            )

        sections.append(
            ReportSection(
                title="Asset Location Scenarios",
                paragraphs=(
                    "Re-runs Three Paths under alternate Roth return assumptions (sensitivity; does not re-allocate balances).",
                ),
                tables=(
                    ReportTable(
                        headers=["Scenario", "Roth return", "Best path", "Best after-tax", "PV taxes (start-year $)"],
                        rows=tuple(rows),
                    ),
                ),
            )
        )

    # --- Objective summary ---
    sections.append(
        ReportSection(
            title="Objective Summary",
            paragraphs=(
                f"Objective: {objective_pick.objective}",
                f"Best by objective: Path {objective_pick.best_label} ({objective_pick.best_path_name})",
            ),
        )
    )

    # --- Longevity sensitivity ---
    if bool(inputs.reporting.longevity_sensitivity_enabled):
        horizons = tuple(int(x) for x in inputs.reporting.longevity_horizons_years)
        rows: list[tuple[str, str, str, str, str]] = []
        for h in horizons:
            p = run_three_paths(inputs=inputs, horizon_years=h)
            picks = pick_best_path(inputs=inputs, labeled_paths=(("A", p.path_a), ("B", p.path_b), ("C", p.path_c)))
            rows.append(
                (
                    str(h),
                    f"{picks.best_label} ({picks.best_path_name})",
                    _basis_money(inputs=inputs, nominal=float(p.path_a["after_tax"]), real=float(p.path_a.get("after_tax_today", p.path_a["after_tax"]))),
                    _basis_money(inputs=inputs, nominal=float(p.path_b["after_tax"]), real=float(p.path_b.get("after_tax_today", p.path_b["after_tax"]))),
                    _basis_money(inputs=inputs, nominal=float(p.path_c["after_tax"]), real=float(p.path_c.get("after_tax_today", p.path_c["after_tax"]))),
                )
            )

        sections.append(
            ReportSection(
                title="Longevity Sensitivity",
                paragraphs=(
                    "Re-runs Three Paths at multiple horizons.",
                ),
                tables=(
                    ReportTable(
                        headers=["Horizon (yrs)", "Best", "A after-tax", "B after-tax", "C after-tax"],
                        rows=tuple(rows),
                    ),
                ),
            )
        )

    # --- 32% question ---

    sections.append(
        ReportSection(
            title="32% Question (Breakeven)",
            paragraphs=(
                "Compares lifetime tax paid for a conservative strategy (stay ≤24%) vs an aggressive strategy (allow 32%).",
                "Breakeven year is the first year when aggressive cumulative tax paid becomes lower than conservative.",
            ),
            tables=(
                ReportTable(
                    headers=["Metric", "Value"],
                    rows=(
                        ("Conservative lifetime tax", _money(breakeven.conservative)),
                        ("Aggressive lifetime tax", _money(breakeven.aggressive)),
                        ("Breakeven", f"Year {breakeven.year}" if breakeven.year is not None else "Not reached"),
                    ),
                ),
            ),
        )
    )

    # --- Home purchase ---
    home_inflation_end = float(home.yearly_data[-1].get("inflation_multiplier", 1.0)) if home.yearly_data else 1.0
    sections.append(
        ReportSection(
            title="Home Purchase Scenario",
            paragraphs=(
                f"Home purchase year: {home.purchase_year}",
                f"Down payment: {_money(home.down_payment)}",
            ),
            tables=(
                ReportTable(
                    headers=["Metric", "Value"],
                    rows=(
                        (
                            "After-tax wealth",
                            _basis_money(inputs=inputs, nominal=home.after_tax, real=home.after_tax / home_inflation_end),
                        ),
                        ("Legacy", _basis_money(inputs=inputs, nominal=home.legacy, real=home.legacy / home_inflation_end)),
                        ("Total conversions", _money(home.total_conversions)),
                        ("Total RMDs", _money(home.total_rmds)),
                        ("Total RMD tax", _money(home.total_rmd_tax)),
                    ),
                ),
            ),
        )
    )

    # --- Tax inputs appendix ---
    start_year = int(inputs.household.start_year)
    # The report's built-in analyses use a 25-year horizon by default.
    report_horizon_years = 25
    end_year = start_year + report_horizon_years - 1

    resolved_tax_year_start = tax_tables.resolve_tax_year(start_year)
    resolved_tax_year_end = tax_tables.resolve_tax_year(end_year)
    resolved_premium_year_start = irmaa_tables.resolve_premium_year(start_year)
    resolved_premium_year_end = irmaa_tables.resolve_premium_year(end_year)
    irmaa_lookback_years = int(
        irmaa_tables.load_irmaa_table(premium_year=resolved_premium_year_start)["irmaa"].get("lookback_years", 2)
    )

    rows: list[tuple[str, str]] = [
        ("Start year (requested)", str(start_year)),
        ("End year (requested)", str(end_year)),
        ("Tax filing status (start)", str(inputs.household.tax_filing_status)),
        (
            "Ordinary income tax table year (resolved)",
            f"start={resolved_tax_year_start}, end={resolved_tax_year_end}",
        ),
        (
            "IRMAA table year (resolved)",
            f"start={resolved_premium_year_start}, end={resolved_premium_year_end}",
        ),
        ("IRMAA lookback", f"{irmaa_lookback_years} years"),
        (
            "Tax table resolution policy",
            "Use latest pinned year ≤ requested year",
        ),
        (
            "Tax payment policy",
            f"income_tax={inputs.tax_payment_policy.income_tax_payment_source}, conversion_tax={inputs.tax_payment_policy.conversion_tax_payment_source}",
        ),
        (
            "NIIT",
            (
                "disabled"
                if not bool(inputs.niit.enabled)
                else f"enabled; realized NII ≈ taxable_return × {float(inputs.niit.nii_fraction_of_return):g} × {float(inputs.niit.realization_fraction):g}"
            ),
        ),
        (
            "Roth conversion 5-year rule",
            (
                "disabled"
                if not bool(inputs.roth_rules.enabled)
                else f"enabled; policy={inputs.roth_rules.policy}, wait_years={int(inputs.roth_rules.conversion_wait_years)}, qualified_age≈{int(inputs.roth_rules.qualified_age_years)}, penalty_rate={float(inputs.roth_rules.penalty_rate):g}"
            ),
        ),
        (
            "Charity/QCD",
            (
                "disabled"
                if not bool(inputs.charity.enabled)
                else f"enabled; annual_amount={_money(float(inputs.charity.annual_amount))}, use_qcd={bool(inputs.charity.use_qcd)}, eligible_age={int(inputs.charity.qcd_eligible_age)}, cap_per_person={_money(float(inputs.charity.qcd_annual_cap_per_person))}"
            ),
        ),
        (
            "Heirs",
            (
                "disabled"
                if not bool(inputs.heirs.enabled)
                else f"enabled; distribution_years={int(inputs.heirs.distribution_years)}, heir_tax_rate={float(inputs.heirs.heir_tax_rate):g}"
            ),
        ),
        (
            "Widow event",
            (
                "disabled"
                if not bool(inputs.widow_event.enabled)
                else f"enabled; widow_year={inputs.widow_event.widow_year}, survivor={inputs.widow_event.survivor}, income_need_multiplier={float(inputs.widow_event.income_need_multiplier):g}"
            ),
        ),
        (
            "Value basis",
            str(inputs.reporting.value_basis),
        ),
    ]
    sections.append(
        ReportSection(
            title="Tax Inputs & Assumptions",
            paragraphs=(
                "Appendix: pinned inputs and key tax-related configuration values used by this run.",
                "This is intended to support auditability and year-over-year tax law updates.",
            ),
            tables=(
                ReportTable(headers=["Item", "Value"], rows=tuple(rows)),
            ),
        )
    )

    final_sections = _filter_sections(
        sections,
        include_sections=include_sections,
        exclude_sections=exclude_sections,
    )

    return ReportDocument(title=title, created_at=created_at, sections=final_sections)
