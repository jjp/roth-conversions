from __future__ import annotations


def simulate_inherited_distribution_after_tax(
    *,
    pretax_balance: float,
    distribution_years: int,
    pretax_return: float,
    beneficiary_tax_rate: float,
    beneficiary_taxable_return: float,
) -> float:
    """Simulate a simplified inherited account distribution.

    Assumptions:
    - The inherited account grows at `pretax_return`.
    - The beneficiary withdraws in equal installments to fully distribute by the end.
    - Withdrawals are taxed at a flat effective rate `beneficiary_tax_rate`.
    - After-tax proceeds are reinvested in a taxable account growing at `beneficiary_taxable_return`.

    Returns the beneficiary's taxable account balance at the end of the distribution window.
    """

    if distribution_years <= 0:
        raise ValueError("distribution_years must be > 0")
    if pretax_balance <= 0:
        return 0.0
    if not (0.0 <= beneficiary_tax_rate <= 1.0):
        raise ValueError("beneficiary_tax_rate must be between 0 and 1")

    ira = float(pretax_balance)
    beneficiary_taxable = 0.0

    for year in range(distribution_years):
        remaining = distribution_years - year
        ira *= (1.0 + float(pretax_return))

        withdrawal = ira / float(remaining)
        ira -= withdrawal

        beneficiary_taxable += withdrawal * (1.0 - float(beneficiary_tax_rate))
        beneficiary_taxable *= (1.0 + float(beneficiary_taxable_return))

    return max(0.0, beneficiary_taxable)


def simulate_inherited_roth_after_tax(
    *,
    roth_balance: float,
    distribution_years: int,
    roth_return: float,
    beneficiary_taxable_return: float,
) -> float:
    """Simplified inherited Roth distribution (tax-free withdrawals)."""

    return simulate_inherited_distribution_after_tax(
        pretax_balance=roth_balance,
        distribution_years=distribution_years,
        pretax_return=roth_return,
        beneficiary_tax_rate=0.0,
        beneficiary_taxable_return=beneficiary_taxable_return,
    )
