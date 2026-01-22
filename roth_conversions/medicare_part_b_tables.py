from __future__ import annotations

import json
from pathlib import Path


data_dir = Path(__file__).parent / "data" / "medicare"


def _available_premium_years() -> tuple[int, ...]:
    if not data_dir.exists():
        return ()
    years: list[int] = []
    for p in data_dir.glob("part_b_base_premium_*.json"):
        try:
            year_str = p.stem.split("_")[-1]
            years.append(int(year_str))
        except Exception:
            continue
    return tuple(sorted(set(years)))


def resolve_part_b_premium_year(requested_year: int) -> int:
    """Resolve to the best available pinned Part B base premium year.

    Strategy: use the latest pinned year <= requested_year; if none, raise.
    """

    requested_year = int(requested_year)
    years = _available_premium_years()
    if not years:
        raise RuntimeError(f"No pinned Part B base premium tables found in {data_dir}")

    candidates = [y for y in years if y <= requested_year]
    if candidates:
        return max(candidates)

    raise ValueError(
        f"No pinned Part B base premium tables for year <= {requested_year}. Available: {', '.join(map(str, years))}"
    )


def load_part_b_base_premium_table(*, premium_year: int) -> dict:
    year = resolve_part_b_premium_year(int(premium_year))
    path = data_dir / f"part_b_base_premium_{year}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def get_part_b_base_premium_monthly(*, premium_year: int) -> float:
    """Return the standard Medicare Part B base premium, monthly.

    Notes:
    - This is the standard base premium (not income-related add-ons / IRMAA).
    - Late enrollment penalties, special cases, and plan-specific adjustments are not modeled.
    """

    table = load_part_b_base_premium_table(premium_year=premium_year)
    return float(table["part_b"]["base_premium_monthly"])
