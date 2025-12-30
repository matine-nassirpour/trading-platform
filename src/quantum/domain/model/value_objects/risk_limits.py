from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.model.exceptions.validation_exceptions import InvariantViolation
from quantum.domain.model.value_objects.base import ValueObject
from quantum.domain.model.value_objects.money import Money


@dataclass(frozen=True)
class RiskLimits(ValueObject):
    """
    Canonical desk-level risk limits.

    Invariants:
    - All limits strictly positive
    - Currency consistency
    """

    max_drawdown: Money
    max_notional: Money
    max_daily_loss: Money

    def _validate(self) -> None:
        currency = self.max_drawdown.currency

        for name, limit in {
            "max_drawdown": self.max_drawdown,
            "max_notional": self.max_notional,
            "max_daily_loss": self.max_daily_loss,
        }.items():
            if not isinstance(limit, Money):
                raise InvariantViolation(f"{name} must be a Money value")

            if limit.currency != currency:
                raise InvariantViolation("All risk limits must share the same currency")

            if limit.value <= Decimal("0"):
                raise InvariantViolation(f"{name} must be strictly positive")
