from __future__ import annotations


def allocate_ira_basis_pro_rata(*, ira_balance: float, basis_remaining: float, amount: float) -> tuple[float, float, float]:
    """Allocate after-tax IRA basis pro-rata to a distribution/conversion.

    Returns:
        taxable_amount, nontaxable_amount, new_basis_remaining

    Notes:
    - This is a simplified pro-rata model based on a single aggregated IRA balance and basis.
    - If `ira_balance <= 0` or `basis_remaining <= 0`, the full `amount` is treated as taxable.
    - If `basis_remaining >= ira_balance`, the full `amount` is treated as non-taxable.

    Example (Frank Kistner):
        ira_balance=175k, basis=100k, amount=40k
        taxable = (75/175)*40 = 17.142857...
        nontaxable = (100/175)*40 = 22.857142...
        basis_after = 77.142857...
    """

    a = max(0.0, float(amount))
    ira = max(0.0, float(ira_balance))
    basis = max(0.0, float(basis_remaining))

    if a <= 0.0:
        return 0.0, 0.0, basis

    if ira <= 0.0 or basis <= 0.0:
        return a, 0.0, basis

    if basis >= ira:
        nontaxable = a
        taxable = 0.0
        basis_after = max(0.0, basis - nontaxable)
        return taxable, nontaxable, basis_after

    nontaxable = a * (basis / ira)
    taxable = a - nontaxable
    basis_after = max(0.0, basis - nontaxable)
    return taxable, nontaxable, basis_after
