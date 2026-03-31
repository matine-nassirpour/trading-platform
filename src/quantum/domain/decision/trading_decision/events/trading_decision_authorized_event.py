from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.decision.authorization.decision_authorization_basis import (
    DecisionAuthorizationBasis,
)
from quantum.domain.decision.common.decision_event import DecisionEvent
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class TradingDecisionAuthorizedEvent(DecisionEvent):
    """
    Emitted when a trade-candidate decision is authorized for downstream use.
    """

    event_name: ClassVar[str] = "decision.trading_decision.authorized"
    event_version: ClassVar[int] = 1

    authorization_basis: DecisionAuthorizationBasis

    def _validate_payload(self) -> None:
        if not isinstance(self.authorization_basis, DecisionAuthorizationBasis):
            raise InvariantViolation(
                "TradingDecisionAuthorizedEvent.authorization_basis invalid"
            )
