from dataclasses import dataclass

from quantum.domain.decision.common.trading_context import TradingContext
from quantum.domain.decision.qualification.decision_qualification import (
    DecisionQualification,
)
from quantum.domain.decision.trading_decision.states.trading_decision_state_base import (
    TradingDecisionStateBase,
)
from quantum.domain.market.instrument.identity.symbol import Symbol
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class TradingDecisionPendingEvaluationState(TradingDecisionStateBase):
    """
    Decision exists but has not yet been resolved to either:
    - trade candidate
    - no trade
    """

    symbol: Symbol
    decision_qualification: DecisionQualification
    context: TradingContext

    def _validate_semantics(self) -> None:
        super()._validate_semantics()

        if self.last_sequence.is_initial():
            raise InvariantViolation(
                "Pending-evaluation TradingDecision cannot have initial sequence"
            )

        if not isinstance(self.symbol, Symbol):
            raise InvariantViolation(
                "TradingDecisionPendingEvaluationState.symbol invalid"
            )

        if not isinstance(self.decision_qualification, DecisionQualification):
            raise InvariantViolation(
                "TradingDecisionPendingEvaluationState.decision_qualification invalid"
            )

        if not isinstance(self.context, TradingContext):
            raise InvariantViolation(
                "TradingDecisionPendingEvaluationState.context invalid"
            )
