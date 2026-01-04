from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.risk.value_objects.risk_threshold_policy import RiskThresholdPolicy
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.monetary_amount import MonetaryAmount
from quantum.domain.shared_kernel.primitives.value_object import ValueObject


@dataclass(frozen=True)
class RiskLimits(ValueObject):
    """
    Canonical desk-level risk limits.

    Properties:
    - All limits are monetary thresholds
    - Limits are NOT algebraic quantities
    - All limits must share the same currency
    """

    max_drawdown: MonetaryAmount
    max_notional: MonetaryAmount
    max_daily_loss: MonetaryAmount
    threshold_policy: RiskThresholdPolicy = RiskThresholdPolicy.inclusive()

    def _validate(self) -> None:
        currency = self.max_drawdown.currency

        for name, limit in {
            "max_drawdown": self.max_drawdown,
            "max_notional": self.max_notional,
            "max_daily_loss": self.max_daily_loss,
        }.items():
            if not isinstance(limit, MonetaryAmount):
                raise InvariantViolation(f"{name} must be a MonetaryAmount")

            if limit.currency != currency:
                raise InvariantViolation("All risk limits must share the same currency")

            if limit.value <= Decimal("0"):
                raise InvariantViolation(f"{name} must be strictly positive")
