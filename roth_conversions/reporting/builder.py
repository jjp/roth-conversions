from __future__ import annotations

from datetime import datetime

import re
from typing import Iterable, Sequence

from ..analysis.bracket32 import find_tax_breakeven_year
from ..analysis.home_purchase import project_with_home_purchase
from ..analysis.three_paths import run_three_paths
from ..models import HouseholdInputs, Strategy
from .models import ReportDocument, ReportSection, ReportTable


def _money(x: float) -> str:
    return f"${x:,.0f}"


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
        "32% Question (Breakeven)",
        "Home Purchase Scenario",
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
    best_label, best_path = max(path_rows, key=lambda r: float(r[1]["after_tax"]))
    summary_lines = [
        f"- Best after-tax wealth: Path {best_label} ({best_path['path_name']}) at {_money(float(best_path['after_tax']))}",
        f"- B − A (after-tax): {_money(paths.path_b['after_tax'] - paths.path_a['after_tax'])}",
        f"- C − A (after-tax): {_money(paths.path_c['after_tax'] - paths.path_a['after_tax'])}",
        "- 32% breakeven: "
        + (f"Year {breakeven.year}" if breakeven.year is not None else "Not reached"),
        f"- Home purchase scenario: after-tax {_money(home.after_tax)}, legacy {_money(home.legacy)}",
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
                    headers=["Path", "Strategy", "After-tax wealth", "Legacy", "First RMD"],
                    rows=(
                        ("A", paths.path_a["path_name"], _money(paths.path_a["after_tax"]), _money(paths.path_a["legacy"]), _money(paths.path_a["first_rmd"])),
                        ("B", paths.path_b["path_name"], _money(paths.path_b["after_tax"]), _money(paths.path_b["legacy"]), _money(paths.path_b["first_rmd"])),
                        ("C", paths.path_c["path_name"], _money(paths.path_c["after_tax"]), _money(paths.path_c["legacy"]), _money(paths.path_c["first_rmd"])),
                    ),
                ),
                ReportTable(
                    headers=["Delta", "Value"],
                    rows=(
                        ("B − A (after-tax)", _money(paths.path_b["after_tax"] - paths.path_a["after_tax"])),
                        ("C − A (after-tax)", _money(paths.path_c["after_tax"] - paths.path_a["after_tax"])),
                    ),
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
                        ("After-tax wealth", _money(home.after_tax)),
                        ("Legacy", _money(home.legacy)),
                        ("Total conversions", _money(home.total_conversions)),
                        ("Total RMDs", _money(home.total_rmds)),
                        ("Total RMD tax", _money(home.total_rmd_tax)),
                    ),
                ),
            ),
        )
    )

    final_sections = _filter_sections(
        sections,
        include_sections=include_sections,
        exclude_sections=exclude_sections,
    )

    return ReportDocument(title=title, created_at=created_at, sections=final_sections)
