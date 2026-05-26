from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.risk_governance.attribution.risk_reference import RiskReference
from quantum.domain.risk_governance.attribution.risk_source_type import RiskSourceType
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class RiskSource(ValueObject):
    """
    Concrete origin of a risk.

    HARD INVARIANT:
    - source type must match reference namespace.
      Example:
        RiskSourceType.strategy() requires RiskReference("strategy:...")
    """

    type: RiskSourceType
    reference: RiskReference

    def _validate_semantics(self) -> None:
        if not isinstance(self.type, RiskSourceType):
            raise InvariantViolation("RiskSource.type must be RiskSourceType")

        if not isinstance(self.reference, RiskReference):
            raise InvariantViolation("RiskSource.reference must be RiskReference")

        if self.type.value != self.reference.namespace():
            raise InvariantViolation(
                "RiskSource type/reference mismatch: "
                f"type={self.type.value!r}, "
                f"reference namespace={self.reference.namespace()!r}"
            )

    @staticmethod
    def strategy(strategy_id: str) -> RiskSource:
        return RiskSource(
            type=RiskSourceType.strategy(),
            reference=RiskReference.strategy(strategy_id),
        )

    @staticmethod
    def instrument(symbol: str) -> RiskSource:
        return RiskSource(
            type=RiskSourceType.instrument(),
            reference=RiskReference.instrument(symbol),
        )

    @staticmethod
    def position(position_id: str) -> RiskSource:
        return RiskSource(
            type=RiskSourceType.position(),
            reference=RiskReference.position(position_id),
        )

    @staticmethod
    def portfolio(portfolio_id: str) -> RiskSource:
        return RiskSource(
            type=RiskSourceType.portfolio(),
            reference=RiskReference.portfolio(portfolio_id),
        )

    @staticmethod
    def session(session_id: str) -> RiskSource:
        return RiskSource(
            type=RiskSourceType.session(),
            reference=RiskReference.session(session_id),
        )

    @staticmethod
    def external(reference_id: str) -> RiskSource:
        return RiskSource(
            type=RiskSourceType.external(),
            reference=RiskReference.external(reference_id),
        )
