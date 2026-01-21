from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


data_dir = Path(__file__).parent / "data" / "medicare"


@dataclass(frozen=True)
class IrmaaTier:
    magi_max: float
    part_b_irmaa_add_monthly: float
    part_d_irmaa_add_monthly: float


def _as_tiers(rows: Iterable[dict]) -> tuple[IrmaaTier, ...]:
    out: list[IrmaaTier] = []
    for row in rows:
        magi_max = row.get("magi_max")
        out.append(
            IrmaaTier(
                magi_max=float("inf") if magi_max is None else float(magi_max),
                part_b_irmaa_add_monthly=float(row["part_b_irmaa_add_monthly"]),
                part_d_irmaa_add_monthly=float(row["part_d_irmaa_add_monthly"]),
            )
        )
    return tuple(out)


def _available_premium_years() -> tuple[int, ...]:
    if not data_dir.exists():
        return ()
    years: list[int] = []
    for p in data_dir.glob("irmaa_*.json"):
        try:
            year_str = p.stem.split("_")[-1]
            years.append(int(year_str))
        except Exception:
            continue
    return tuple(sorted(set(years)))


def resolve_premium_year(requested_year: int) -> int:
    """Resolve to the best available pinned premium year.

    Strategy: use the latest pinned year <= requested_year; if none, raise.
    """

    requested_year = int(requested_year)
    years = _available_premium_years()
    if not years:
        raise RuntimeError(f"No pinned IRMAA tables found in {data_dir}")

    candidates = [y for y in years if y <= requested_year]
    if candidates:
        return max(candidates)

    raise ValueError(
        f"No pinned IRMAA tables for year <= {requested_year}. Available: {', '.join(map(str, years))}"
    )


def load_irmaa_table(*, premium_year: int) -> dict:
    year = resolve_premium_year(int(premium_year))
    path = data_dir / f"irmaa_{year}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def get_irmaa_addons_monthly(*, premium_year: int, filing_status: str, magi: float) -> tuple[float, float]:
    """Return (Part B IRMAA add-on, Part D IRMAA add-on), monthly.

    Values are incremental add-ons (not the base Part B premium, and not the Part D plan premium).
    """

    table = load_irmaa_table(premium_year=premium_year)
    tiers_by_status = table["irmaa"]["tiers"]
    try:
        tiers = _as_tiers(tiers_by_status[str(filing_status)])
    except KeyError as e:
        raise ValueError(f"Unsupported filing_status={filing_status!r} in pinned IRMAA table") from e

    income = float(magi)
    for t in tiers:
        if income <= float(t.magi_max):
            return float(t.part_b_irmaa_add_monthly), float(t.part_d_irmaa_add_monthly)

    # Should be unreachable due to final tier magi_max=inf
    return float(tiers[-1].part_b_irmaa_add_monthly), float(tiers[-1].part_d_irmaa_add_monthly)
