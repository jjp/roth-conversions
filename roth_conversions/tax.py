from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .tax_tables import (
    TaxBracket as PinnedBracket,
    calculate_tax as calculate_tax_from_brackets,
    get_ordinary_income_brackets,
    marginal_rate as marginal_rate_from_brackets,
)


@dataclass(frozen=True)
class TaxBracket:
    """Backwards-compatible bracket model (kept for public API stability)."""

    ceiling: float
    rate: float


def _to_legacy(brackets: Sequence[PinnedBracket]) -> tuple[TaxBracket, ...]:
    return tuple(TaxBracket(b.ceiling, b.rate) for b in brackets)


def calculate_tax(taxable_income: float, brackets: Sequence[TaxBracket]) -> float:
    """Piecewise tax on taxable income using progressive brackets."""

    return calculate_tax_from_brackets(taxable_income, brackets)


def marginal_rate(taxable_income: float, brackets: Sequence[TaxBracket]) -> float:
    return marginal_rate_from_brackets(taxable_income, brackets)


def calculate_tax_ordinary_income(*, taxable_income: float, tax_year: int, filing_status: str) -> float:
    brackets = _to_legacy(get_ordinary_income_brackets(tax_year=tax_year, filing_status=filing_status))
    return calculate_tax_from_brackets(taxable_income, brackets)


def marginal_rate_ordinary_income(*, taxable_income: float, tax_year: int, filing_status: str) -> float:
    brackets = _to_legacy(get_ordinary_income_brackets(tax_year=tax_year, filing_status=filing_status))
    return marginal_rate_from_brackets(taxable_income, brackets)


# --- Backwards compatible wrappers used throughout the codebase/tests ---


def calculate_tax_mfj_2024(taxable_income: float) -> float:
    return calculate_tax_ordinary_income(taxable_income=taxable_income, tax_year=2024, filing_status="MFJ")


def marginal_rate_mfj_2024(taxable_income: float) -> float:
    return marginal_rate_ordinary_income(taxable_income=taxable_income, tax_year=2024, filing_status="MFJ")
