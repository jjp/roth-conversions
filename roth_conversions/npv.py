from __future__ import annotations


def npv(values: list[float], *, discount_rate: float) -> float:
    """Compute net present value with year-0 timing.

    values[t] is discounted by (1 + discount_rate) ** t.
    """

    r = float(discount_rate)
    if r <= -0.99:
        raise ValueError("discount_rate must be > -0.99")

    total = 0.0
    for t, v in enumerate(values):
        total += float(v) / ((1.0 + r) ** t)
    return float(total)
