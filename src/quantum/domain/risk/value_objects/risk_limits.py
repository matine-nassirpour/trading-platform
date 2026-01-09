from dataclasses import dataclass

from quantum.domain.risk.value_objects.risk_threshold_policy import RiskThresholdPolicy
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.money.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)
from quantum.domain.shared_kernel.money.money_context import MoneyContext


@dataclass(frozen=True)
class RiskLimits:
    """
    Canonical desk-level risk limits.

    Properties:
    - All limits are monetary thresholds
    - Limits are NOT algebraic quantities
    - All limits must share the same currency
    """

    context: MoneyContext
    max_drawdown: ContextualMonetaryAmount
    max_notional: ContextualMonetaryAmount
    max_daily_loss: ContextualMonetaryAmount
    threshold_policy: RiskThresholdPolicy

    def __post_init__(self) -> None:
        for name, limit in {
            "max_drawdown": self.max_drawdown,
            "max_notional": self.max_notional,
            "max_daily_loss": self.max_daily_loss,
        }.items():
            if limit.context != self.context:
                raise InvariantViolation(
                    f"{name} MoneyContext mismatch: {limit.context} vs {self.context}"
                )
