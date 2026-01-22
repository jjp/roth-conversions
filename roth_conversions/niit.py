from __future__ import annotations

NIIT_RATE = 0.038


def niit_threshold(*, filing_status: str) -> float:
    """NIIT MAGI thresholds (not inflation-indexed).

    Supported statuses: MFJ, Single.
    """

    status = str(filing_status)
    if status == "MFJ":
        return 250_000.0
    if status == "Single":
        return 200_000.0
    # Fallback: assume MFJ-like threshold for unknown statuses.
    return 250_000.0


def calculate_niit(*, magi: float, net_investment_income: float, filing_status: str) -> float:
    """Compute NIIT (3.8%) using a simplified NII input.

    NIIT applies to the lesser of:
    - net investment income
    - MAGI in excess of threshold
    """

    income = max(0.0, float(net_investment_income))
    excess = max(0.0, float(magi) - niit_threshold(filing_status=filing_status))
    base = min(income, excess)
    return base * NIIT_RATE
