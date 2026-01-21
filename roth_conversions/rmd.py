from __future__ import annotations

from typing import Final


RMD_DIVISORS: Final[dict[int, float]] = {
    72: 27.4,
    73: 26.5,
    74: 25.5,
    75: 24.6,
    76: 23.7,
    77: 22.9,
    78: 22.0,
    79: 21.1,
    80: 20.2,
    81: 19.4,
    82: 18.5,
    83: 17.7,
    84: 16.8,
    85: 16.0,
    86: 15.2,
    87: 14.4,
    88: 13.7,
    89: 12.9,
    90: 12.2,
    91: 11.5,
    92: 10.8,
    93: 10.1,
    94: 9.5,
    95: 8.9,
}


def rmd_divisor(age: int) -> float | None:
    """Return Uniform Lifetime Table divisor for the given age.

    Notebook logic: no RMD required if age < 73.
    For ages > 95, it uses 8.9.
    """
    if int(age) < 73:
        return None
    return float(RMD_DIVISORS.get(int(age), 8.9))


def required_minimum_distribution(ira_balance: float, age: int) -> float:
    divisor = rmd_divisor(age)
    if divisor is None:
        return 0.0
    bal = float(ira_balance)
    if bal <= 0:
        return 0.0
    return bal / divisor
