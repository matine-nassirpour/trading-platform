from dataclasses import dataclass

from quantum.domain.decision.context.trading_context import TradingContext
from quantum.domain.decision.governance.decision_authorization_result import (
    DecisionAuthorizationResult,
)
from quantum.domain.decision.identity.decision_identity import DecisionIdentity
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.identifiers.intent_id import IntentId
from quantum.domain.shared_kernel.value_objects.symbol import Symbol
from quantum.domain.trading.execution.order.position_side import PositionSide
from quantum.domain.trading.intent.trading_intent_state_base import (
    TradingIntentStateBase,
)


@dataclass(frozen=True, slots=True)
class TradingIntentInitializedState(TradingIntentStateBase):

    intent_id: IntentId
    symbol: Symbol
    side: PositionSide

    decision_identity: DecisionIdentity
    context: TradingContext

    authorization_result: DecisionAuthorizationResult | None

    def _validate(self) -> None:
        if self.last_sequence.is_initial():
            raise InvariantViolation(
                "Initialized TradingIntent cannot have initial sequence"
            )

    # --- Semantic helpers -----------------------------------------------------

    def is_evaluated(self) -> bool:
        return self.authorization_result is not None

    def is_authorized(self) -> bool:
        return (
            self.authorization_result is not None
            and self.authorization_result.is_authorized()
        )

    def is_rejected(self) -> bool:
        return (
            self.authorization_result is not None
            and self.authorization_result.is_rejected()
        )
