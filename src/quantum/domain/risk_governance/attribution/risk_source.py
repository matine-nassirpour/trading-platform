from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.risk_governance.attribution.risk_reference import RiskReference
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class RiskSource(ValueObject):
    """
    Canonical origin of risk.

    Namespace is derived exclusively from RiskReference.
    """

    reference: RiskReference

    def _validate_semantics(self) -> None:
        if not isinstance(self.reference, RiskReference):
            raise InvariantViolation("RiskSource.reference must be RiskReference")

    @property
    def type(self) -> str:
        return self.reference.namespace()

    @property
    def identifier(self) -> str:
        return self.reference.identifier()

    @staticmethod
    def strategy(strategy_id: str) -> RiskSource:
        return RiskSource(reference=RiskReference.strategy(strategy_id))

    @staticmethod
    def instrument(symbol: str) -> RiskSource:
        return RiskSource(reference=RiskReference.instrument(symbol))

    @staticmethod
    def position(position_id: str) -> RiskSource:
        return RiskSource(reference=RiskReference.position(position_id))

    @staticmethod
    def portfolio(portfolio_id: str) -> RiskSource:
        return RiskSource(reference=RiskReference.portfolio(portfolio_id))

    @staticmethod
    def session(session_id: str) -> RiskSource:
        return RiskSource(reference=RiskReference.session(session_id))

    @staticmethod
    def external(reference_id: str) -> RiskSource:
        return RiskSource(reference=RiskReference.external(reference_id))
