from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared.errors.invariants import InvariantViolation
from quantum.domain.shared.primitives.monetary_value_object import MonetaryValueObject
from quantum.domain.shared.primitives.value_object import ValueObject


@dataclass(frozen=True)
class RiskLimits(ValueObject):
    """
    Canonical desk-level risk limits.
    """

    max_drawdown: MonetaryValueObject
    max_notional: MonetaryValueObject
    max_daily_loss: MonetaryValueObject

    def _validate(self) -> None:
        currency = self.max_drawdown.currency

        for name, limit in {
            "max_drawdown": self.max_drawdown,
            "max_notional": self.max_notional,
            "max_daily_loss": self.max_daily_loss,
        }.items():
            if limit.currency != currency:
                raise InvariantViolation("All risk limits must share the same currency")

            if limit.value <= Decimal("0"):
                raise InvariantViolation(f"{name} must be strictly positive")
