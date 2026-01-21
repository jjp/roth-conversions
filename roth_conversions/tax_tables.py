from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Sequence


data_dir = Path(__file__).parent / "data" / "tax"


@dataclass(frozen=True)
class TaxBracket:
    ceiling: float
    rate: float


def _as_brackets(rows: Iterable[dict]) -> tuple[TaxBracket, ...]:
    out: list[TaxBracket] = []
    for row in rows:
        ceiling = row.get("ceiling")
        out.append(TaxBracket(float("inf") if ceiling is None else float(ceiling), float(row["rate"])))
    return tuple(out)


def _available_tax_years() -> tuple[int, ...]:
    if not data_dir.exists():
        return ()
    years: list[int] = []
    for p in data_dir.glob("us_federal_ordinary_income_*.json"):
        try:
            year_str = p.stem.split("_")[-1]
            years.append(int(year_str))
        except Exception:
            continue
    return tuple(sorted(set(years)))


def resolve_tax_year(requested_year: int) -> int:
    """Resolve to the best available pinned tax year.

    Strategy: use the latest pinned year <= requested_year; if none, raise.

    This keeps runs deterministic while allowing projections starting in later years
    to run (with a stable, known baseline) until you add newer pinned tables.
    """

    requested_year = int(requested_year)
    years = _available_tax_years()
    if not years:
        raise RuntimeError(f"No pinned tax tables found in {data_dir}")

    candidates = [y for y in years if y <= requested_year]
    if candidates:
        return max(candidates)

    raise ValueError(
        f"No pinned tax tables for year <= {requested_year}. Available: {', '.join(map(str, years))}"
    )


def load_ordinary_income_table(*, tax_year: int) -> dict:
    year = resolve_tax_year(int(tax_year))
    path = data_dir / f"us_federal_ordinary_income_{year}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def get_ordinary_income_brackets(*, tax_year: int, filing_status: str) -> tuple[TaxBracket, ...]:
    table = load_ordinary_income_table(tax_year=tax_year)
    brackets = table["ordinary_income"]["brackets"]
    try:
        rows = brackets[str(filing_status)]
    except KeyError as e:
        raise ValueError(f"Unsupported filing_status={filing_status!r} in pinned tax table") from e
    return _as_brackets(rows)


def get_standard_deduction(*, tax_year: int, filing_status: str) -> float:
    table = load_ordinary_income_table(tax_year=tax_year)
    sd = table["ordinary_income"]["standard_deduction"]
    try:
        return float(sd[str(filing_status)])
    except KeyError as e:
        raise ValueError(f"Unsupported filing_status={filing_status!r} in pinned tax table") from e


def get_bracket_ceiling(*, tax_year: int, filing_status: str, rate: float) -> float:
    """Return the taxable-income ceiling for the bracket at `rate`.

    Example: for 2024 MFJ, rate=0.24 => 383900.
    """

    r = float(rate)
    for b in get_ordinary_income_brackets(tax_year=tax_year, filing_status=filing_status):
        if abs(float(b.rate) - r) < 1e-12:
            return float(b.ceiling)
    raise ValueError(f"No bracket found for rate={rate} in tax_year={tax_year}, filing_status={filing_status}")


def calculate_tax(taxable_income: float, brackets: Sequence[TaxBracket]) -> float:
    taxable_income = float(taxable_income)
    if taxable_income <= 0:
        return 0.0

    tax = 0.0
    prev = 0.0
    for bracket in brackets:
        if taxable_income <= prev:
            break
        upper = float(bracket.ceiling)
        amount = min(taxable_income, upper) - prev
        tax += amount * float(bracket.rate)
        prev = upper
    return float(tax)


def marginal_rate(taxable_income: float, brackets: Sequence[TaxBracket]) -> float:
    taxable_income = float(taxable_income)
    if taxable_income <= 0:
        return float(brackets[0].rate)

    for bracket in brackets:
        if taxable_income <= float(bracket.ceiling):
            return float(bracket.rate)
    return float(brackets[-1].rate)
