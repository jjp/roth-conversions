from __future__ import annotations


def gross_up_for_withholding(net_tax: float, marginal_rate: float) -> float:
    """Approximate pre-tax IRA distribution needed to net `net_tax` withheld.

    If marginal_rate is 24%, withholding $24 requires a $100 distribution.
    """

    if net_tax <= 0:
        return 0.0
    r = max(0.0, min(float(marginal_rate), 0.99))
    if r <= 0.0:
        return float(net_tax)
    return float(net_tax) / (1.0 - r)


def pay_tax(
    *,
    taxable: float,
    ira: float,
    tax_due: float,
    source: str,
    minimum_cash_reserve: float,
    marginal_rate: float,
) -> tuple[float, float]:
    """Pay a tax/expense amount from the chosen source.

    - source="taxable": pay from taxable above cash reserve; spillover to IRA gross-up.
    - source="ira": pay via IRA withholding gross-up.

    Returns updated (taxable, ira).
    """

    if tax_due <= 0:
        return taxable, ira

    if source == "taxable":
        available_cash = max(0.0, float(taxable) - float(minimum_cash_reserve))
        from_taxable = min(float(tax_due), available_cash)
        taxable -= from_taxable
        remaining = float(tax_due) - from_taxable
        if remaining > 0:
            ira -= gross_up_for_withholding(remaining, marginal_rate)
        return taxable, ira

    if source == "ira":
        ira -= gross_up_for_withholding(float(tax_due), marginal_rate)
        return taxable, ira

    raise ValueError(f"unsupported tax payment source: {source!r}")
