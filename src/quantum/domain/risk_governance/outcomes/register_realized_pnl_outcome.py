from dataclasses import dataclass

from quantum.domain.risk_governance.breach_detection.breaches.risk_breach import (
    RiskBreach,
)
from quantum.domain.risk_governance.portfolio_state.risk_snapshot import RiskSnapshot
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class RegisterRealizedPnLOutcome(ValueObject):
    """
    Semantic domain outcome of registering realized PnL.

    Application handlers must consume this outcome instead of inspecting
    concrete RiskGovernance event types.
    """

    resulting_snapshot: RiskSnapshot
    active_breaches: tuple[RiskBreach, ...]
    insolvency_declared: bool

    def _validate_semantics(self) -> None:
        if not isinstance(self.resulting_snapshot, RiskSnapshot):
            raise InvariantViolation(
                "RegisterRealizedPnLOutcome.resulting_snapshot must be RiskSnapshot"
            )

        if not isinstance(self.active_breaches, tuple):
            raise InvariantViolation(
                "RegisterRealizedPnLOutcome.active_breaches must be tuple[RiskBreach, ...]"
            )

        for breach in self.active_breaches:
            if not isinstance(breach, RiskBreach):
                raise InvariantViolation(
                    "RegisterRealizedPnLOutcome.active_breaches must contain only RiskBreach"
                )

        if type(self.insolvency_declared) is not bool:
            raise InvariantViolation(
                "RegisterRealizedPnLOutcome.insolvency_declared must be bool"
            )
