from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class StrategyEligibilityDTO:
    eligible: bool
    reason: str


@dataclass(frozen=True, slots=True)
class CapitalAllocationDTO:
    capital_fraction: Decimal
    risk_budget: Decimal


@dataclass(frozen=True, slots=True)
class KillSwitchStatusDTO:
    status: str
    reason: str | None
