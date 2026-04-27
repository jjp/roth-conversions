from __future__ import annotations

import argparse
from pathlib import Path

from roth_conversions.config import load_inputs
from roth_conversions.analysis.three_paths import run_three_paths
from roth_conversions.analysis.bracket32 import find_tax_breakeven_year
from roth_conversions.analysis.home_purchase import project_with_home_purchase
from roth_conversions.models import Strategy
from roth_conversions.objectives import pick_best_path
from roth_conversions.projection import project_with_tax_tracking
from roth_conversions.reporting.builder import build_report, list_default_report_sections
from roth_conversions.reporting.render_markdown import render_markdown


def _money(x: float) -> str:
    return f"${x:,.0f}"


def cmd_three_paths(args: argparse.Namespace) -> int:
    inputs = load_inputs(args.config)
    paths = run_three_paths(
        inputs=inputs,
        path_b_annual=args.path_b_annual,
        path_b_years=args.path_b_years,
        path_c_annual=args.path_c_annual,
        path_c_years=args.path_c_years,
        horizon_years=args.horizon_years,
    )

    obj = pick_best_path(
        inputs=inputs,
        labeled_paths=(("A", paths.path_a), ("B", paths.path_b), ("C", paths.path_c)),
    )

    print("\nTHREE PATHS (A/B/C)")
    print(f"Objective: {obj.objective} (value_basis={inputs.reporting.value_basis})")
    for label, p in [("A", paths.path_a), ("B", paths.path_b), ("C", paths.path_c)]:
        print(
            f"Path {label} ({p['path_name']}): after-tax={_money(p['after_tax'])} | "
            f"legacy={_money(p['legacy'])} | first_rmd={_money(p['first_rmd'])}"
        )

    print(f"Best by objective: Path {obj.best_label} ({obj.best_path_name})")

    print(f"\nB vs A delta: {_money(paths.path_b['after_tax'] - paths.path_a['after_tax'])}")
    print(f"C vs A delta: {_money(paths.path_c['after_tax'] - paths.path_a['after_tax'])}")
    return 0


def cmd_32pct(args: argparse.Namespace) -> int:
    inputs = load_inputs(args.config)

    conservative = Strategy("Conservative (100K x 5, ≤24%)", 100_000, 5, allow_32_bracket=False)
    aggressive = Strategy("Aggressive (175K x 8, allow 32%)", 175_000, 8, allow_32_bracket=True)

    breakeven = find_tax_breakeven_year(inputs=inputs, conservative=conservative, aggressive=aggressive)
    print("\n32% QUESTION")
    print(f"Conservative lifetime tax: {_money(breakeven.conservative)}")
    print(f"Aggressive lifetime tax:   {_money(breakeven.aggressive)}")
    if breakeven.year is None:
        print("Breakeven: not reached within horizon")
    else:
        print(f"Breakeven: year {breakeven.year}")

    # Also print wealth comparison
    cons_res = project_with_tax_tracking(inputs=inputs, strategy=conservative)
    agg_res = project_with_tax_tracking(inputs=inputs, strategy=aggressive)
    print(f"Aggressive after-tax delta vs conservative: {_money(agg_res.after_tax - cons_res.after_tax)}")
    print(f"Aggressive legacy delta vs conservative:    {_money(agg_res.legacy - cons_res.legacy)}")
    return 0


def cmd_home(args: argparse.Namespace) -> int:
    inputs = load_inputs(args.config)
    scenario = project_with_home_purchase(
        inputs=inputs,
        purchase_year=args.purchase_year,
        down_payment=args.down_payment,
        conversion_years=args.conversion_years,
        max_annual_conv=args.max_annual_conv,
        horizon_years=args.horizon_years,
    )

    print("\nHOME PURCHASE")
    print(f"Purchase year: {scenario.purchase_year} | down payment: {_money(scenario.down_payment)}")
    print(f"After-tax wealth: {_money(scenario.after_tax)}")
    print(f"Legacy:           {_money(scenario.legacy)}")
    print(f"Total conversions: {_money(scenario.total_conversions)}")
    print(f"Total RMDs:        {_money(scenario.total_rmds)}")
    print(f"Total RMD tax:     {_money(scenario.total_rmd_tax)}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    if args.list_sections:
        print("\nREPORT SECTIONS")
        for key, title in list_default_report_sections():
            print(f"- {key}: {title}")
        return 0

    inputs = load_inputs(args.config)

    includes = args.include or None
    excludes = args.exclude or None
    doc = build_report(
        inputs=inputs,
        home_down_payment=float(args.home_down_payment),
        home_purchase_year=int(args.home_purchase_year),
        include_sections=includes,
        exclude_sections=excludes,
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if args.format == "md":
        out_path.write_text(render_markdown(doc), encoding="utf-8")
        print(f"Wrote Markdown report to: {out_path}")
        return 0

    if args.format == "pdf":
        from roth_conversions.reporting.render_pdf import render_pdf

        render_pdf(doc, out_path=out_path)
        print(f"Wrote PDF report to: {out_path}")
        return 0

    raise ValueError(f"Unsupported format: {args.format}")


def add_roth_subcommands(parent_subparsers: argparse._SubParsersAction) -> None:
    """Register the `roth` command group and its subcommands."""

    roth = parent_subparsers.add_parser(
        "roth",
        help="Roth conversion analysis",
        description="Roth conversion analysis (library refactor)",
    )
    roth.add_argument("--config", required=True, help="Path to TOML/JSON config (retirement_config.template.toml format)")

    sub = roth.add_subparsers(dest="cmd", required=True)

    p3 = sub.add_parser("three-paths", help="Run Chapter 3 A/B/C paths")
    p3.add_argument("--path-b-annual", type=float, default=100_000)
    p3.add_argument("--path-b-years", type=int, default=5)
    p3.add_argument("--path-c-annual", type=float, default=150_000)
    p3.add_argument("--path-c-years", type=int, default=10)
    p3.add_argument("--horizon-years", type=int, default=25)
    p3.set_defaults(func=cmd_three_paths)

    p32 = sub.add_parser("32pct", help="Run Chapter 9 32%% breakeven question")
    p32.set_defaults(func=cmd_32pct)

    ph = sub.add_parser("home", help="Run Chapter 8 home purchase scenario")
    ph.add_argument("--down-payment", type=float, default=200_000)
    ph.add_argument("--purchase-year", type=int, default=2027)
    ph.add_argument("--conversion-years", type=int, default=5)
    ph.add_argument("--max-annual-conv", type=float, default=150_000)
    ph.add_argument("--horizon-years", type=int, default=25)
    ph.set_defaults(func=cmd_home)

    pr = sub.add_parser("report", help="Build an email-ready report (Markdown or PDF)")
    pr.add_argument("--format", choices=["pdf", "md"], default="pdf")
    pr.add_argument("--out", default=str(Path("outputs") / "report.pdf"))
    pr.add_argument("--home-down-payment", type=float, default=200_000)
    pr.add_argument("--home-purchase-year", type=int, default=2027)
    pr.add_argument(
        "--include",
        action="append",
        default=[],
        help="Include only these section(s) (repeatable, or comma-separated); use --list-sections to see keys",
    )
    pr.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Exclude these section(s) (repeatable, or comma-separated); use --list-sections to see keys",
    )
    pr.add_argument(
        "--list-sections",
        action="store_true",
        help="Print available report section keys and exit",
    )
    pr.set_defaults(func=cmd_report)
