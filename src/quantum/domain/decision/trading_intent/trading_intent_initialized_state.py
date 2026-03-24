from dataclasses import dataclass

from quantum.domain.decision.context.trading_context import TradingContext
from quantum.domain.decision.governance.decision_authorization_result import (
    DecisionAuthorizationResult,
)
from quantum.domain.decision.identity.decision_identity import DecisionIdentity
from quantum.domain.decision.trading_intent.trading_intent_state_base import (
    TradingIntentStateBase,
)
from quantum.domain.market.instrument.symbol import Symbol
from quantum.domain.market.value_objects.position_side import PositionSide
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class TradingIntentInitializedState(TradingIntentStateBase):
    """
    Identity-free initialized state for TradingIntent.

    Doctrine:
    - The aggregate root is the sole canonical owner of aggregate identity.
    - This state contains business state ONLY.
    """

    symbol: Symbol
    side: PositionSide

    decision_identity: DecisionIdentity
    context: TradingContext

    authorization_result: DecisionAuthorizationResult | None

    def _validate_types(self) -> None:

        if not isinstance(self.symbol, Symbol):
            raise InvariantViolation("TradingIntentInitializedState.symbol invalid")

        if not isinstance(self.side, PositionSide):
            raise InvariantViolation("TradingIntentInitializedState.side invalid")

        if not isinstance(self.decision_identity, DecisionIdentity):
            raise InvariantViolation(
                "TradingIntentInitializedState.decision_identity invalid"
            )

        if not isinstance(self.context, TradingContext):
            raise InvariantViolation("TradingIntentInitializedState.context invalid")

        if self.authorization_result is not None and not isinstance(
            self.authorization_result,
            DecisionAuthorizationResult,
        ):
            raise InvariantViolation(
                "TradingIntentInitializedState.authorization_result invalid"
            )

    def _validate_semantics(self) -> None:
        super()._validate_semantics()
        self._validate_types()

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
