from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RothConversionBucket:
    year_index: int  # 0-based model year when the conversion occurred
    remaining: float


@dataclass
class RothLedger:
    """Tracks Roth conversion buckets for a simplified 5-year rule model.

    Simplifications:
    - Treat starting Roth balance as withdrawable basis (penalty-free, tax-free).
    - Track conversions as separate buckets (oldest-first ordering).
    - If withdrawing conversion principal within `conversion_wait_years` AND age < qualified_age,
      apply a 10% penalty on the portion withdrawn from those "young" buckets.

    This models the most common planning concern Frank flags: needing to tap converted
    principal soon after conversion.
    """

    basis_remaining: float
    buckets: list[RothConversionBucket]

    def deposit_conversion(self, *, amount: float, year_index: int) -> None:
        amt = max(0.0, float(amount))
        if amt <= 0:
            return
        self.buckets.append(RothConversionBucket(year_index=year_index, remaining=amt))

    def available_penalty_free(self, *, year_index: int, conversion_wait_years: int) -> float:
        cutoff = int(year_index) - int(conversion_wait_years)
        eligible = sum(b.remaining for b in self.buckets if b.year_index <= cutoff)
        return max(0.0, float(self.basis_remaining) + float(eligible))

    def withdraw(
        self,
        *,
        requested: float,
        year_index: int,
        conversion_wait_years: int,
        qualified_age_years: int,
        household_age_years: int,
        policy: str,
    ) -> tuple[float, float]:
        """Withdraw from Roth following ordering; return (actual_withdrawn, penalty_base).

        policy:
        - "penalty": allow withdrawal from young conversion buckets but penalize when age < qualified_age.
        - "prevent": disallow withdrawal from young conversion buckets (forces other funding sources).
        """

        req = max(0.0, float(requested))
        if req <= 0:
            return 0.0, 0.0

        policy_str = str(policy)
        if policy_str not in {"penalty", "prevent"}:
            raise ValueError(f"invalid roth_rules.policy={policy_str!r}; expected 'penalty' or 'prevent'")

        if policy_str == "prevent":
            allowed = self.available_penalty_free(year_index=year_index, conversion_wait_years=conversion_wait_years)
            req = min(req, allowed)

        withdrawn = 0.0
        penalty_base = 0.0

        # 1) contributions/basis
        from_basis = min(req, max(0.0, float(self.basis_remaining)))
        self.basis_remaining -= from_basis
        withdrawn += from_basis
        req -= from_basis

        if req <= 0:
            return withdrawn, 0.0

        # 2) conversions (oldest first)
        for bucket in self.buckets:
            if req <= 0:
                break
            if bucket.remaining <= 0:
                continue

            take = min(req, bucket.remaining)
            bucket.remaining -= take
            withdrawn += take
            req -= take

            age = int(household_age_years)
            if age < int(qualified_age_years):
                young = (int(year_index) - int(bucket.year_index)) < int(conversion_wait_years)
                if young:
                    penalty_base += take

        # 3) earnings (not modeled separately); any remaining req is ignored here.
        return withdrawn, penalty_base
