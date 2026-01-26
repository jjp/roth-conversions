from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
import tarfile
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

# Allow running as: `python scripts/run_scenario_packets.py`
# (When running a script, Python puts the script directory on sys.path, not the repo root.)
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from roth_conversions.analysis.bracket32 import find_tax_breakeven_year
from roth_conversions.analysis.home_purchase import project_with_home_purchase
from roth_conversions.analysis.three_paths import run_three_paths
from roth_conversions.config import inputs_to_dict, load_inputs
from roth_conversions.models import Strategy
from roth_conversions.objectives import pick_best_path
from roth_conversions.reporting.builder import build_report
from roth_conversions.reporting.render_markdown import render_markdown
from roth_conversions.reporting.render_pdf import render_pdf


@dataclass(frozen=True)
class ScenarioSpec:
    scenario_id: str
    config_path: Path


def _discover_configs(configs_dir: Path, pattern: str) -> tuple[Path, ...]:
    return tuple(sorted(configs_dir.glob(pattern)))


def _is_excluded_config(path: Path, *, exclude_names: set[str]) -> bool:
    return path.name in exclude_names


def _timestamp_slug(dt: datetime | None = None) -> str:
    dt = dt or datetime.now()
    return dt.strftime("%Y-%m-%d_%H%M%S")


def _ensure_new_dir(path: Path) -> None:
    if path.exists():
        raise FileExistsError(str(path))
    path.mkdir(parents=True, exist_ok=False)


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def _iter_yearly_rows(path_result: dict) -> Iterable[dict[str, Any]]:
    yearly = path_result.get("yearly_details") or []
    if isinstance(yearly, list):
        for row in yearly:
            if isinstance(row, dict):
                yield row


def _write_yearly_csv(path: Path, *, scenario_id: str, label: str, path_result: dict) -> None:
    # Provide stable, accountant-friendly headers.
    # Note: projection.py currently emits hardcoded keys rajesh_age/terri_age; we also export generic aliases.
    columns = [
        "scenario_id",
        "path",
        "year",
        "calendar_year",
        "inflation_multiplier",
        "spouse1_age",
        "spouse2_age",
        "ss_income",
        "rmd",
        "from_ira",
        "qcd",
        "charity_need",
        "from_taxable",
        "from_roth",
        "conversion",
        "conversion_tax",
        "income_tax",
        "state_tax",
        "irmaa_cost",
        "medicare_part_b_base_premium_cost",
        "niit_tax",
        "roth_penalty_tax",
        "magi",
        "investment_income",
        "ira_end",
        "roth_end",
        "taxable_end",
    ]

    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        w.writeheader()

        for row in _iter_yearly_rows(path_result):
            out = dict(row)
            out["scenario_id"] = scenario_id
            out["path"] = label

            # Aliases (current internal keys are legacy)
            out["spouse1_age"] = out.get("spouse1_age", out.get("rajesh_age"))
            out["spouse2_age"] = out.get("spouse2_age", out.get("terri_age"))

            w.writerow(out)


def _path_summary(path_result: dict) -> dict[str, Any]:
    keys = [
        "path_name",
        "after_tax",
        "after_tax_today",
        "legacy",
        "legacy_today",
        "heirs_after_tax",
        "heirs_after_tax_today",
        "first_rmd",
        "total_conversions",
        "total_conversion_tax",
        "effective_conv_rate",
        "total_rmds",
        "total_rmd_tax",
        "total_irmaa_cost",
        "total_medicare_part_b_base_premium_cost",
        "total_state_tax",
        "total_niit_tax",
        "total_roth_penalty_tax",
        "npv_taxes_today",
    ]
    return {k: path_result.get(k) for k in keys}


def build_packet(
    spec: ScenarioSpec,
    *,
    out_root: Path,
    home_purchase_year: int,
    home_down_payment: float,
    report_format: str,
) -> dict[str, Any]:
    inputs = load_inputs(spec.config_path)

    paths = run_three_paths(inputs=inputs)
    labeled_paths = (("A", paths.path_a), ("B", paths.path_b), ("C", paths.path_c))
    pick = pick_best_path(inputs=inputs, labeled_paths=labeled_paths)

    conservative = Strategy("Conservative (100K x 5, ≤24%)", 100_000, 5, allow_32_bracket=False)
    aggressive = Strategy("Aggressive (175K x 8, allow 32%)", 175_000, 8, allow_32_bracket=True)
    breakeven = find_tax_breakeven_year(inputs=inputs, conservative=conservative, aggressive=aggressive)

    home = project_with_home_purchase(
        inputs=inputs,
        purchase_year=int(home_purchase_year),
        down_payment=float(home_down_payment),
    )

    # Report is the main human-readable artifact.
    doc = build_report(inputs=inputs, home_down_payment=home_down_payment, home_purchase_year=home_purchase_year)

    scenario_dir = out_root / spec.scenario_id
    scenario_dir.mkdir(parents=True, exist_ok=True)

    # Copy config as ground truth input.
    inputs_dir = scenario_dir / "inputs"
    inputs_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(spec.config_path, inputs_dir / spec.config_path.name)
    shutil.copy2(spec.config_path, inputs_dir / "config.toml")

    # Also emit parsed inputs as JSON (useful for diffing + audits).
    _write_json(scenario_dir / "inputs_parsed.json", inputs_to_dict(inputs))

    # Write report.
    report_pdf_path = scenario_dir / "report.pdf"
    report_md_path = scenario_dir / "report.md"

    if report_format in {"pdf", "both"}:
        try:
            render_pdf(doc, out_path=report_pdf_path)
        except RuntimeError as e:
            raise RuntimeError(
                "PDF output requested but PDF renderer is unavailable. "
                "Install reportlab (uv add reportlab; uv sync) or rerun with --report-format md"
            ) from e

    if report_format in {"md", "both"}:
        report_md_path.write_text(render_markdown(doc), encoding="utf-8")

    # Write yearly CSVs (accountant-friendly).
    _write_yearly_csv(scenario_dir / "yearly_path_a.csv", scenario_id=spec.scenario_id, label="A", path_result=paths.path_a)
    _write_yearly_csv(scenario_dir / "yearly_path_b.csv", scenario_id=spec.scenario_id, label="B", path_result=paths.path_b)
    _write_yearly_csv(scenario_dir / "yearly_path_c.csv", scenario_id=spec.scenario_id, label="C", path_result=paths.path_c)

    summary: dict[str, Any] = {
        "scenario_id": spec.scenario_id,
        "config": str(spec.config_path.as_posix()),
        "config_filename": spec.config_path.name,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "household": {
            "tax_filing_status": str(inputs.household.tax_filing_status),
            "start_year": int(inputs.household.start_year),
            "discount_rate": float(inputs.household.discount_rate),
        },
        "people": {
            "spouse1": {
                "name": str(inputs.spouse1.name),
                "age": int(inputs.spouse1.age),
                "ss_start_age": int(inputs.spouse1.ss_start_age),
                "ss_annual": float(inputs.spouse1.ss_annual),
            },
            "spouse2": {
                "name": str(inputs.spouse2.name),
                "age": int(inputs.spouse2.age),
                "ss_start_age": int(inputs.spouse2.ss_start_age),
                "ss_annual": float(inputs.spouse2.ss_annual),
            },
        },
        "toggles": {
            "irmaa_enabled": bool(inputs.medicare.irmaa_enabled),
            "part_b_base_premium_enabled": bool(getattr(inputs.medicare, "part_b_base_premium_enabled", False)),
            "niit_enabled": bool(inputs.niit.enabled),
            "state_tax_enabled": bool(getattr(inputs, "state_tax", None)) and bool(inputs.state_tax.enabled),
            "qcd_enabled": bool(inputs.charity.enabled) and bool(inputs.charity.use_qcd),
            "charity_enabled": bool(inputs.charity.enabled),
            "heirs_enabled": bool(inputs.heirs.enabled),
            "widow_event_enabled": bool(inputs.widow_event.enabled),
            "roth_5yr_rule_enabled": bool(inputs.roth_rules.enabled),
            "asset_location_enabled": bool(getattr(inputs, "asset_location", None)) and bool(inputs.asset_location.enabled),
            "itemized_deductions_enabled": bool(getattr(inputs, "itemized_deductions", None)) and bool(inputs.itemized_deductions.enabled),
        },
        "toggle_details": {
            "state_tax": {
                "rate": float(inputs.state_tax.rate),
                "base": str(inputs.state_tax.base),
            },
            "niit": {
                "nii_fraction_of_return": float(inputs.niit.nii_fraction_of_return),
                "realization_fraction": float(inputs.niit.realization_fraction),
            },
            "charity": {
                "annual_amount": float(inputs.charity.annual_amount),
                "use_qcd": bool(inputs.charity.use_qcd),
                "qcd_eligible_age": float(inputs.charity.qcd_eligible_age),
                "qcd_annual_cap_per_person": float(inputs.charity.qcd_annual_cap_per_person),
            },
            "heirs": {
                "distribution_years": int(inputs.heirs.distribution_years),
                "heir_tax_rate": float(inputs.heirs.heir_tax_rate),
            },
            "widow_event": {
                "widow_year": inputs.widow_event.widow_year,
                "survivor": str(inputs.widow_event.survivor),
                "income_need_multiplier": float(inputs.widow_event.income_need_multiplier),
            },
            "roth_rules": {
                "policy": str(inputs.roth_rules.policy),
                "conversion_wait_years": int(inputs.roth_rules.conversion_wait_years),
                "qualified_age_years": int(inputs.roth_rules.qualified_age_years),
                "penalty_rate": float(inputs.roth_rules.penalty_rate),
            },
        },
        "objective": {
            "objective": pick.objective,
            "value_basis": str(inputs.reporting.value_basis),
            "best_label": pick.best_label,
            "best_path_name": pick.best_path_name,
        },
        "three_paths": {
            "A": _path_summary(paths.path_a),
            "B": _path_summary(paths.path_b),
            "C": _path_summary(paths.path_c),
        },
        "artifacts": {
            "report_pdf": (str(report_pdf_path.name) if report_format in {"pdf", "both"} else None),
            "report_md": (str(report_md_path.name) if report_format in {"md", "both"} else None),
            "yearly_path_a_csv": "yearly_path_a.csv",
            "yearly_path_b_csv": "yearly_path_b.csv",
            "yearly_path_c_csv": "yearly_path_c.csv",
        },
        "home_purchase": {
            "purchase_year": int(home.purchase_year),
            "down_payment": float(home.down_payment),
            "after_tax": float(home.after_tax),
            "legacy": float(home.legacy),
            "total_conversions": float(home.total_conversions),
            "total_rmds": float(home.total_rmds),
            "total_rmd_tax": float(home.total_rmd_tax),
        },
        "breakeven_32pct": {
            "conservative_lifetime_tax": float(breakeven.conservative),
            "aggressive_lifetime_tax": float(breakeven.aggressive),
            "breakeven_year": breakeven.year,
        },
        "notes": {
            "breakeven_32pct_in_report": True,
        },
    }

    _write_json(scenario_dir / "summary.json", summary)
    return summary


def _iter_files_recursive(root: Path) -> Iterable[Path]:
    for p in root.rglob("*"):
        if p.is_file():
            yield p


def _write_zip_archive(*, source_dir: Path, archive_path: Path) -> None:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, mode="w", compression=zipfile.ZIP_DEFLATED) as z:
        for file_path in _iter_files_recursive(source_dir):
            rel = file_path.relative_to(source_dir)
            z.write(file_path, arcname=str(Path(source_dir.name) / rel))


def _write_tar_archive(*, source_dir: Path, archive_path: Path) -> None:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    mode = "w:gz" if archive_path.suffix.lower().endswith("gz") else "w"
    with tarfile.open(archive_path, mode=mode) as t:
        t.add(source_dir, arcname=source_dir.name)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build accountant-friendly scenario packets (inputs + reports + yearly CSVs).")
    p.add_argument("--configs-dir", default="configs", help="Directory containing scenario configs")
    p.add_argument(
        "--pattern",
        default="retirement_config*.toml",
        help="Glob pattern (within configs-dir) to select configs",
    )
    p.add_argument(
        "--exclude",
        action="append",
        default=["retirement_config.template.toml"],
        help="Config filename(s) to exclude (repeatable)",
    )
    p.add_argument(
        "--out-root",
        default=None,
        help="Output root directory (default: timestamped folder under outputs/)",
    )
    p.add_argument(
        "--archive-format",
        choices=["zip", "tar"],
        default="zip",
        help="Archive format for the single bundle output",
    )
    p.add_argument(
        "--archive-out",
        default=None,
        help="Archive file to write (default: outputs/scenario_packets_<timestamp>.zip or .tar)",
    )
    p.add_argument("--home-purchase-year", type=int, default=2027)
    p.add_argument("--home-down-payment", type=float, default=200_000)
    p.add_argument(
        "--report-format",
        choices=["pdf", "md", "both"],
        default="pdf",
        help="Which report format(s) to write into each scenario packet",
    )

    args = p.parse_args(argv)

    configs_dir = Path(args.configs_dir)
    ts = _timestamp_slug()
    out_root = Path(str(args.out_root)) if args.out_root else (Path("outputs") / f"scenario_packets_{ts}")
    _ensure_new_dir(out_root)

    exclude_names = {str(x) for x in (args.exclude or [])}
    cfgs_all = _discover_configs(configs_dir, str(args.pattern))
    cfgs = tuple(c for c in cfgs_all if not _is_excluded_config(c, exclude_names=exclude_names))
    if not cfgs:
        raise SystemExit(f"No configs matched: {configs_dir / args.pattern}")

    specs = [ScenarioSpec(scenario_id=cfg.stem, config_path=cfg) for cfg in cfgs]

    summaries: list[dict[str, Any]] = []
    for spec in specs:
        print(f"Building packet: {spec.scenario_id}")
        summaries.append(
            build_packet(
                spec,
                out_root=out_root,
                home_purchase_year=int(args.home_purchase_year),
                home_down_payment=float(args.home_down_payment),
                report_format=str(args.report_format),
            )
        )

    # Top-level README for the bundle.
    readme_path = out_root / "README.md"
    readme_path.write_text(
        "\n".join(
            [
                "# Scenario packet bundle",
                "",
                "This folder (and its paired .zip archive) contains input configs and generated outputs for accountant validation.",
                "",
                "## Contents",
                "- `manifest.csv`: rollup of scenario toggles and key metadata",
                "- One folder per scenario: `<scenario_id>/`",
                "  - `inputs/`: copied config(s)",
                "  - `report.pdf`: primary accountant-facing report",
                "  - `yearly_path_[a|b|c].csv`: year-by-year exports for validation",
                "  - `summary.json`: machine-readable summary",
                "",
                "## Validation hints",
                "Typical checks:",
                "- Confirm config assumptions (returns, inflation, filing status, toggles)",
                "- Validate yearly MAGI and tax components (income tax, conversion tax, IRMAA, NIIT, state tax)",
                "- Validate RMD timing/amounts and end-of-year balances",
                "",
                "Notes:",
                "- This is comparative planning output, not tax preparation advice.",
                "- Tax tables are pinned/resolved; see `Tax Inputs & Assumptions` inside each report.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    # Write an index CSV for quick scanning.
    index_path = out_root / "index.csv"
    index_cols = [
        "scenario_id",
        "objective",
        "value_basis",
        "best_label",
        "A_after_tax",
        "B_after_tax",
        "C_after_tax",
        "A_legacy",
        "B_legacy",
        "C_legacy",
    ]

    with index_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=index_cols)
        w.writeheader()
        for s in summaries:
            tp = s.get("three_paths", {})
            w.writerow(
                {
                    "scenario_id": s.get("scenario_id"),
                    "objective": (s.get("objective") or {}).get("objective"),
                    "value_basis": (s.get("objective") or {}).get("value_basis"),
                    "best_label": (s.get("objective") or {}).get("best_label"),
                    "A_after_tax": (tp.get("A") or {}).get("after_tax"),
                    "B_after_tax": (tp.get("B") or {}).get("after_tax"),
                    "C_after_tax": (tp.get("C") or {}).get("after_tax"),
                    "A_legacy": (tp.get("A") or {}).get("legacy"),
                    "B_legacy": (tp.get("B") or {}).get("legacy"),
                    "C_legacy": (tp.get("C") or {}).get("legacy"),
                }
            )

    print(f"Wrote scenario index: {index_path}")

    # Write a manifest CSV that includes scenario toggles/metadata.
    manifest_path = out_root / "manifest.csv"
    manifest_cols = [
        "scenario_id",
        "config_filename",
        "tax_filing_status",
        "start_year",
        "objective",
        "value_basis",
        "best_label",
        "irmaa_enabled",
        "part_b_base_premium_enabled",
        "niit_enabled",
        "state_tax_enabled",
        "charity_enabled",
        "qcd_enabled",
        "heirs_enabled",
        "widow_event_enabled",
        "roth_5yr_rule_enabled",
        "asset_location_enabled",
        "itemized_deductions_enabled",
        "state_tax_rate",
        "state_tax_base",
        "charity_annual_amount",
        "heirs_distribution_years",
        "heirs_tax_rate",
        "widow_year",
    ]
    with manifest_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=manifest_cols)
        w.writeheader()
        for s in summaries:
            hh = s.get("household") or {}
            tg = s.get("toggles") or {}
            td = s.get("toggle_details") or {}
            st = td.get("state_tax") or {}
            ch = td.get("charity") or {}
            he = td.get("heirs") or {}
            we = td.get("widow_event") or {}
            obj = s.get("objective") or {}
            w.writerow(
                {
                    "scenario_id": s.get("scenario_id"),
                    "config_filename": s.get("config_filename"),
                    "tax_filing_status": hh.get("tax_filing_status"),
                    "start_year": hh.get("start_year"),
                    "objective": obj.get("objective"),
                    "value_basis": obj.get("value_basis"),
                    "best_label": obj.get("best_label"),
                    "irmaa_enabled": tg.get("irmaa_enabled"),
                    "part_b_base_premium_enabled": tg.get("part_b_base_premium_enabled"),
                    "niit_enabled": tg.get("niit_enabled"),
                    "state_tax_enabled": tg.get("state_tax_enabled"),
                    "charity_enabled": tg.get("charity_enabled"),
                    "qcd_enabled": tg.get("qcd_enabled"),
                    "heirs_enabled": tg.get("heirs_enabled"),
                    "widow_event_enabled": tg.get("widow_event_enabled"),
                    "roth_5yr_rule_enabled": tg.get("roth_5yr_rule_enabled"),
                    "asset_location_enabled": tg.get("asset_location_enabled"),
                    "itemized_deductions_enabled": tg.get("itemized_deductions_enabled"),
                    "state_tax_rate": st.get("rate"),
                    "state_tax_base": st.get("base"),
                    "charity_annual_amount": ch.get("annual_amount"),
                    "heirs_distribution_years": he.get("distribution_years"),
                    "heirs_tax_rate": he.get("heir_tax_rate"),
                    "widow_year": we.get("widow_year"),
                }
            )
    print(f"Wrote scenario manifest: {manifest_path}")

    # Create a single archive containing the entire packet directory.
    if args.archive_out:
        archive_path = Path(str(args.archive_out))
    else:
        ext = "zip" if str(args.archive_format) == "zip" else "tar"
        archive_path = Path("outputs") / f"scenario_packets_{ts}.{ext}"

    if str(args.archive_format) == "zip":
        _write_zip_archive(source_dir=out_root, archive_path=archive_path)
    else:
        _write_tar_archive(source_dir=out_root, archive_path=archive_path)

    print(f"Wrote scenario archive: {archive_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
