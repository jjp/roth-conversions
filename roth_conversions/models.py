from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Sequence


@dataclass(frozen=True)
class SpouseInputs:
    name: str
    age: int
    traditional_ira: float
    sep_ira: float
    roth_ira: float
    ss_start_age: int
    ss_annual: float

    @property
    def pretax_ira_total(self) -> float:
        return float(self.traditional_ira) + float(self.sep_ira)


@dataclass(frozen=True)
class Household:
    tax_filing_status: str = "MFJ"
    start_year: int = 2025
    discount_rate: float = 0.0


@dataclass(frozen=True)
class ReportingInputs:
    value_basis: str = "nominal"  # "nominal" | "real" (start-year dollars)


@dataclass(frozen=True)
class JointAccounts:
    taxable_accounts: float


@dataclass(frozen=True)
class PlanInputs:
    monthly_income_need: float
    minimum_cash_reserve: float

    @property
    def annual_income_need(self) -> float:
        return float(self.monthly_income_need) * 12.0


@dataclass(frozen=True)
class ReturnAssumptions:
    inflation_rate: float
    taxable_return: float
    ira_return: float
    roth_return: float


@dataclass(frozen=True)
class TaxPaymentPolicy:
    """Policy for how taxes are paid.

    Values:
    - "taxable": pay from taxable account (respecting minimum cash reserve; remainder from IRA)
    - "ira": pay from IRA (grossed up using a marginal-rate approximation)
    """

    income_tax_payment_source: str = "taxable"
    conversion_tax_payment_source: str = "taxable"


@dataclass(frozen=True)
class MedicareInputs:
    irmaa_enabled: bool = False


@dataclass(frozen=True)
class WidowEventInputs:
    enabled: bool = False
    widow_year: int | None = None
    survivor: str = "spouse1"  # "spouse1" | "spouse2" (informational; SS uses max benefit)
    income_need_multiplier: float = 1.0


@dataclass(frozen=True)
class CharitableGivingInputs:
    """Charitable giving and QCD (Qualified Charitable Distribution) assumptions.

    Notes:
    - This model uses whole-year ages. The real-world QCD eligibility is age 70½; we approximate
      with a configurable whole-year threshold (default 71).
    - QCD reduces taxable income / MAGI (excluded from AGI) while still reducing IRA balance.
    """

    enabled: bool = False
    annual_amount: float = 0.0  # start-year dollars
    use_qcd: bool = True
    qcd_eligible_age: int = 71
    qcd_annual_cap_per_person: float = 100_000.0


@dataclass(frozen=True)
class HeirsInputs:
    """Heir modeling assumptions for inherited accounts.

    This is a simplified model intended for strategy comparisons:
    - inherited IRA/Roth must be distributed within `distribution_years`
    - IRA distributions are taxed at `heir_tax_rate` (flat effective rate)
    - after-tax proceeds are assumed to be reinvested in a taxable account
    """

    enabled: bool = False
    distribution_years: int = 10  # common values: 5 or 10
    heir_tax_rate: float = 0.30


@dataclass(frozen=True)
class HouseholdInputs:
    household: Household
    spouse1: SpouseInputs
    spouse2: SpouseInputs
    joint: JointAccounts
    plan: PlanInputs
    assumptions: ReturnAssumptions
    tax_payment_policy: TaxPaymentPolicy = TaxPaymentPolicy()
    medicare: MedicareInputs = MedicareInputs()
    widow_event: WidowEventInputs = WidowEventInputs()
    reporting: ReportingInputs = ReportingInputs()
    charity: CharitableGivingInputs = CharitableGivingInputs()
    heirs: HeirsInputs = HeirsInputs()

    @property
    def total_pretax(self) -> float:
        return self.spouse1.pretax_ira_total + self.spouse2.pretax_ira_total

    @property
    def total_roth(self) -> float:
        return float(self.spouse1.roth_ira) + float(self.spouse2.roth_ira)

    @property
    def years_to_spouse1_ss(self) -> int:
        return max(0, int(self.spouse1.ss_start_age) - int(self.spouse1.age))

    @property
    def years_to_spouse2_ss(self) -> int:
        return max(0, int(self.spouse2.ss_start_age) - int(self.spouse2.age))

    @property
    def years_to_spouse1_rmd(self) -> int:
        return max(0, 73 - int(self.spouse1.age))

    @property
    def years_to_spouse2_rmd(self) -> int:
        return max(0, 73 - int(self.spouse2.age))


@dataclass(frozen=True)
class Strategy:
    name: str
    annual_conversion: float
    conversion_years: int
    allow_32_bracket: bool = False


@dataclass(frozen=True)
class ProjectionYear:
    year: int
    calendar_year: int
    spouse1_age: int
    spouse2_age: int
    ss_income: float
    rmd: float
    ira_withdrawal: float
    from_taxable: float
    from_roth: float
    conversion: float
    conversion_tax: float
    income_tax: float
    ira_end: float
    roth_end: float
    taxable_end: float
    cumulative_conv_tax: float
    cumulative_rmd_tax: float
    cumulative_total_tax: float
    irmaa_cost: float = 0.0
    income_need: float = 0.0
    inflation_multiplier: float = 1.0
    qcd: float = 0.0
    charity_need: float = 0.0


@dataclass(frozen=True)
class ProjectionResult:
    strategy: Strategy
    total_conversions: float
    total_conv_tax: float
    total_rmds: float
    total_rmd_tax: float
    total_lifetime_tax: float
    after_tax: float
    legacy: float
    yearly: Sequence[ProjectionYear]
    total_irmaa_cost: float = 0.0
    after_tax_today: float = 0.0
    legacy_today: float = 0.0
    npv_spending_today: float = 0.0
    npv_taxes_today: float = 0.0
    heirs_after_tax: float = 0.0
    heirs_after_tax_today: float = 0.0

    def first_rmd(self, *, years_to_first_rmd: int) -> float:
        # If already RMD-eligible at the start year, the first RMD occurs in year 1.
        if years_to_first_rmd <= 0:
            if not self.yearly:
                return 0.0
            return float(self.yearly[0].rmd)
        idx = years_to_first_rmd - 1
        if idx < 0 or idx >= len(self.yearly):
            return 0.0
        return float(self.yearly[idx].rmd)


def clamp_series(series: Optional[Sequence[float]], *, horizon_years: int, name: str) -> Optional[Sequence[float]]:
    if series is None:
        return None
    if len(series) < horizon_years:
        raise ValueError(f"{name} must have length >= horizon_years ({horizon_years})")
    return series


def as_float_seq(values: Optional[Iterable[float]]) -> Optional[list[float]]:
    if values is None:
        return None
    return [float(v) for v in values]
