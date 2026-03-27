from dataclasses import dataclass

from quantum.domain.decision.authorization.decision_authorization_result import (
    DecisionAuthorizationResult,
)
from quantum.domain.decision.common.trading_context import TradingContext
from quantum.domain.decision.qualification.decision_identity import DecisionIdentity
from quantum.domain.decision.trading_decision.states.trading_decision_state_base import (
    TradingDecisionStateBase,
)
from quantum.domain.market.instrument.identity.symbol import Symbol
from quantum.domain.market.positioning.position_side import PositionSide
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class TradingDecisionAuthorizedState(TradingDecisionStateBase):
    """
    Terminal state: decision resolved as trade candidate and authorized.
    """

    symbol: Symbol
    side: PositionSide
    decision_identity: DecisionIdentity
    context: TradingContext
    authorization_result: DecisionAuthorizationResult

    def _validate_semantics(self) -> None:
        super()._validate_semantics()

        if self.last_sequence.is_initial():
            raise InvariantViolation(
                "Authorized TradingDecision cannot have initial sequence"
            )

        if not isinstance(self.symbol, Symbol):
            raise InvariantViolation("TradingDecisionAuthorizedState.symbol invalid")

        if not isinstance(self.side, PositionSide):
            raise InvariantViolation("TradingDecisionAuthorizedState.side invalid")

        if not isinstance(self.decision_identity, DecisionIdentity):
            raise InvariantViolation(
                "TradingDecisionAuthorizedState.decision_identity invalid"
            )

        if not isinstance(self.context, TradingContext):
            raise InvariantViolation("TradingDecisionAuthorizedState.context invalid")

        if not isinstance(self.authorization_result, DecisionAuthorizationResult):
            raise InvariantViolation(
                "TradingDecisionAuthorizedState.authorization_result invalid"
            )

        if not self.authorization_result.is_authorized():
            raise InvariantViolation(
                "TradingDecisionAuthorizedState requires an authorized result"
            )
