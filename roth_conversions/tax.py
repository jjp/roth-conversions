from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class TaxBracket:
    ceiling: float
    rate: float


# Notebook used these as "2024 MFJ brackets".
MFJ_2024_BRACKETS: tuple[TaxBracket, ...] = (
    TaxBracket(23200, 0.10),
    TaxBracket(94300, 0.12),
    TaxBracket(201050, 0.22),
    TaxBracket(383900, 0.24),
    TaxBracket(487450, 0.32),
    TaxBracket(731200, 0.35),
    TaxBracket(float("inf"), 0.37),
)


def calculate_tax(taxable_income: float, brackets: Sequence[TaxBracket]) -> float:
    """Piecewise tax on taxable income using progressive brackets."""
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


def calculate_tax_mfj_2024(taxable_income: float) -> float:
    return calculate_tax(taxable_income, MFJ_2024_BRACKETS)


def marginal_rate_mfj_2024(taxable_income: float) -> float:
    return marginal_rate(taxable_income, MFJ_2024_BRACKETS)
