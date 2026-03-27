from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.decision.authorization.decision_authorization_reason_code import (
    DecisionAuthorizationReasonCode,
)
from quantum.domain.decision.common.decision_event import DecisionEvent
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class TradingDecisionRejectedEvent(DecisionEvent):
    """
    Emitted when a trade-candidate decision is rejected by governance.
    """

    event_name: ClassVar[str] = "decision.trading_decision.rejected"
    event_version: ClassVar[int] = 1

    reason_code: DecisionAuthorizationReasonCode

    def _validate_payload(self) -> None:
        if not isinstance(self.reason_code, DecisionAuthorizationReasonCode):
            raise InvariantViolation("TradingDecisionRejectedEvent.reason_code invalid")
