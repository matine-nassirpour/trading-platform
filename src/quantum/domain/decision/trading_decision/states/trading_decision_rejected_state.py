from dataclasses import dataclass

from quantum.domain.decision.authorization.decision_authorization_result import (
    DecisionAuthorizationResult,
)
from quantum.domain.decision.common.trading_context import TradingContext
from quantum.domain.decision.qualification.decision_qualification import (
    DecisionQualification,
)
from quantum.domain.decision.trading_decision.states.trading_decision_state_base import (
    TradingDecisionStateBase,
)
from quantum.domain.decision.trading_decision.trade_direction import TradeDirection
from quantum.domain.market.instrument.identity.symbol import Symbol
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class TradingDecisionRejectedState(TradingDecisionStateBase):
    """
    Terminal state: decision resolved as trade candidate but rejected by governance.
    """

    symbol: Symbol
    trade_direction: TradeDirection
    decision_qualification: DecisionQualification
    context: TradingContext
    authorization_result: DecisionAuthorizationResult

    def _validate_semantics(self) -> None:
        super()._validate_semantics()

        if self.last_sequence.is_initial():
            raise InvariantViolation(
                "Rejected TradingDecision cannot have initial sequence"
            )

        if not isinstance(self.symbol, Symbol):
            raise InvariantViolation("TradingDecisionRejectedState.symbol invalid")

        if not isinstance(self.trade_direction, TradeDirection):
            raise InvariantViolation(
                "TradingDecisionRejectedState.trade_direction invalid"
            )

        if not isinstance(self.decision_qualification, DecisionQualification):
            raise InvariantViolation(
                "TradingDecisionRejectedState.decision_qualification invalid"
            )

        if not isinstance(self.context, TradingContext):
            raise InvariantViolation("TradingDecisionRejectedState.context invalid")

        if not isinstance(self.authorization_result, DecisionAuthorizationResult):
            raise InvariantViolation(
                "TradingDecisionRejectedState.authorization_result invalid"
            )

        if not self.authorization_result.is_rejected():
            raise InvariantViolation(
                "TradingDecisionRejectedState requires a rejected result"
            )
