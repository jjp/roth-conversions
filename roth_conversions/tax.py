from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .tax_tables import (
    TaxBracket as PinnedBracket,
    calculate_tax as calculate_tax_from_brackets,
    get_ordinary_income_brackets,
    get_ltcg_qd_thresholds,
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


def calculate_tax_federal_ltcg_qd_simple(
    *,
    ordinary_income: float,
    qualified_dividends: float,
    long_term_capital_gains: float,
    deduction: float,
    tax_year: int,
    filing_status: str,
) -> float:
    """Simplified federal income tax: ordinary rates + LTCG/QD preferential stacking.

    Model:
    - Total income = ordinary_income + qualified_dividends + long_term_capital_gains
    - taxable_income = max(0, total_income - deduction)
    - preferential taxable amount = min(qualified_dividends + long_term_capital_gains, taxable_income)
    - ordinary taxable amount = taxable_income - preferential
    - ordinary tax uses ordinary brackets applied to ordinary taxable amount
    - preferential tax uses 0%/15%/20% rates, with thresholds expressed in total taxable income
      (stacking on top of ordinary taxable amount)

    Notes:
    - This intentionally ignores collectibles (28%), unrecaptured §1250 (25%), and other special cases.
    - Thresholds are pinned by year and resolved with the project’s pinned-table policy.
    """

    ordinary_income = float(ordinary_income)
    qualified_dividends = float(qualified_dividends)
    long_term_capital_gains = float(long_term_capital_gains)
    deduction = float(deduction)

    total_income = ordinary_income + qualified_dividends + long_term_capital_gains
    taxable_income = max(0.0, total_income - deduction)

    preferential_total = max(0.0, qualified_dividends + long_term_capital_gains)
    preferential_taxable = min(preferential_total, taxable_income)
    ordinary_taxable = max(0.0, taxable_income - preferential_taxable)

    ordinary_brackets = _to_legacy(get_ordinary_income_brackets(tax_year=tax_year, filing_status=filing_status))
    ordinary_tax = calculate_tax_from_brackets(ordinary_taxable, ordinary_brackets)

    if preferential_taxable <= 0:
        return float(ordinary_tax)

    max_zero, max_15 = get_ltcg_qd_thresholds(tax_year=tax_year, filing_status=filing_status)

    # How much preferential income can fit under the 0% threshold after ordinary taxable income?
    room_zero = max(0.0, float(max_zero) - float(ordinary_taxable))
    amount_zero = min(preferential_taxable, room_zero)

    # Total preferential income that can fit under the 15% threshold after ordinary taxable income.
    room_15_or_less = max(0.0, float(max_15) - float(ordinary_taxable))
    amount_15_or_less = min(preferential_taxable, room_15_or_less)

    amount_15 = max(0.0, amount_15_or_less - amount_zero)
    amount_20 = max(0.0, preferential_taxable - amount_zero - amount_15)

    preferential_tax = amount_15 * 0.15 + amount_20 * 0.20
    return float(ordinary_tax + preferential_tax)


# --- Backwards compatible wrappers used throughout the codebase/tests ---


def calculate_tax_mfj_2024(taxable_income: float) -> float:
    return calculate_tax_ordinary_income(taxable_income=taxable_income, tax_year=2024, filing_status="MFJ")


def marginal_rate_mfj_2024(taxable_income: float) -> float:
    return marginal_rate_ordinary_income(taxable_income=taxable_income, tax_year=2024, filing_status="MFJ")
