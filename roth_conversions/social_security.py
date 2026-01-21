from __future__ import annotations


def taxable_social_security(
    *,
    total_benefits: float,
    other_income: float,
    filing_status: str,
    tax_exempt_interest: float = 0.0,
) -> float:
    """Compute the taxable portion of Social Security benefits.

    Uses the IRS provisional-income method:
    - provisional = other_income + tax_exempt_interest + 0.5 * total_benefits

    Supported filing_status values (initial scope):
    - "MFJ"
    - "Single"

    Returns a value in [0, 0.85 * total_benefits].

    Note: This intentionally ignores some edge cases (e.g., MFS living with spouse).
    """

    ss = max(0.0, float(total_benefits))
    other = max(0.0, float(other_income))
    tax_exempt = max(0.0, float(tax_exempt_interest))

    status = str(filing_status)
    if status == "MFJ":
        base = 32_000.0
        adjusted = 44_000.0
    elif status == "Single":
        base = 25_000.0
        adjusted = 34_000.0
    else:
        raise ValueError(f"Unsupported filing_status for SS taxation: {filing_status!r}")

    provisional = other + tax_exempt + 0.5 * ss

    if provisional <= base:
        return 0.0

    if provisional <= adjusted:
        taxable = 0.5 * (provisional - base)
        return min(taxable, 0.5 * ss)

    # Above adjusted base
    part1 = 0.85 * (provisional - adjusted)
    part2 = min(0.5 * (adjusted - base), 0.5 * ss)
    taxable = part1 + part2
    return min(taxable, 0.85 * ss)
