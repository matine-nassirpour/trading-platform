from dataclasses import dataclass

from quantum.domain.decision.common.trading_context import TradingContext
from quantum.domain.decision.no_trade.no_trade_decision import NoTradeDecision
from quantum.domain.decision.qualification.decision_qualification import (
    DecisionQualification,
)
from quantum.domain.decision.trading_decision.states.trading_decision_state_base import (
    TradingDecisionStateBase,
)
from quantum.domain.market.instrument.identity.symbol import Symbol
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class TradingDecisionNoTradeState(TradingDecisionStateBase):
    """
    Terminal state: decision resolved explicitly as NO-TRADE.
    """

    symbol: Symbol
    decision_qualification: DecisionQualification
    context: TradingContext
    no_trade_decision: NoTradeDecision

    def _validate_semantics(self) -> None:
        super()._validate_semantics()

        if self.last_sequence.is_initial():
            raise InvariantViolation(
                "No-trade TradingDecision cannot have initial sequence"
            )

        if not isinstance(self.symbol, Symbol):
            raise InvariantViolation("TradingDecisionNoTradeState.symbol invalid")

        if not isinstance(self.decision_qualification, DecisionQualification):
            raise InvariantViolation(
                "TradingDecisionNoTradeState.decision_qualification invalid"
            )

        if not isinstance(self.context, TradingContext):
            raise InvariantViolation("TradingDecisionNoTradeState.context invalid")

        if not isinstance(self.no_trade_decision, NoTradeDecision):
            raise InvariantViolation(
                "TradingDecisionNoTradeState.no_trade_decision invalid"
            )
