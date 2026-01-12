from dataclasses import dataclass

from quantum.domain.risk.value_objects.risk_threshold_policy import RiskThresholdPolicy
from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.money.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)
from quantum.domain.shared_kernel.money.money_context import MoneyContext
from quantum.domain.shared_kernel.primitives.value_object import ValueObject


@dataclass(frozen=False)
class RiskLimits(ValueObject):
    """
    Canonical desk-level risk limits.

    Properties:
    - All limits are monetary thresholds
    - Limits are NOT algebraic quantities
    - All limits must share the same MoneyContext
    """

    context: MoneyContext
    max_drawdown: ContextualMonetaryAmount
    max_notional: ContextualMonetaryAmount
    max_daily_loss: ContextualMonetaryAmount
    threshold_policy: RiskThresholdPolicy

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.VALUE_OBJECT

    def _validate_semantics(self) -> None:
        if not isinstance(self.context, MoneyContext):
            raise InvariantViolation("RiskLimits requires a MoneyContext")

        for name, limit in {
            "max_drawdown": self.max_drawdown,
            "max_notional": self.max_notional,
            "max_daily_loss": self.max_daily_loss,
        }.items():
            if not isinstance(limit, ContextualMonetaryAmount):
                raise InvariantViolation(f"{name} must be a ContextualMonetaryAmount")

            if limit.context != self.context:
                raise InvariantViolation(
                    f"{name} MoneyContext mismatch: {limit.context} vs {self.context}"
                )

        if not isinstance(self.threshold_policy, RiskThresholdPolicy):
            raise InvariantViolation("RiskLimits requires a RiskThresholdPolicy")
