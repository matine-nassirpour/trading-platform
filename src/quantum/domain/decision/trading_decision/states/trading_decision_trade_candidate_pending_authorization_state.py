from dataclasses import dataclass

from quantum.domain.decision.common.trading_context import TradingContext
from quantum.domain.decision.qualification.decision_identity import DecisionIdentity
from quantum.domain.decision.trading_decision.states.trading_decision_state_base import (
    TradingDecisionStateBase,
)
from quantum.domain.market.instrument.identity.symbol import Symbol
from quantum.domain.market.positioning.position_side import PositionSide
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class TradingDecisionTradeCandidatePendingAuthorizationState(TradingDecisionStateBase):
    """
    Trade candidate exists and is awaiting governance authorization.
    """

    symbol: Symbol
    side: PositionSide
    decision_identity: DecisionIdentity
    context: TradingContext

    def _validate_semantics(self) -> None:
        super()._validate_semantics()

        if self.last_sequence.is_initial():
            raise InvariantViolation(
                "Trade-candidate TradingDecision cannot have initial sequence"
            )

        if not isinstance(self.symbol, Symbol):
            raise InvariantViolation(
                "TradingDecisionTradeCandidatePendingAuthorizationState.symbol invalid"
            )

        if not isinstance(self.side, PositionSide):
            raise InvariantViolation(
                "TradingDecisionTradeCandidatePendingAuthorizationState.side invalid"
            )

        if not isinstance(self.decision_identity, DecisionIdentity):
            raise InvariantViolation(
                "TradingDecisionTradeCandidatePendingAuthorizationState.decision_identity invalid"
            )

        if not isinstance(self.context, TradingContext):
            raise InvariantViolation(
                "TradingDecisionTradeCandidatePendingAuthorizationState.context invalid"
            )
