from collections.abc import Sequence

from quantum.application.decision.commands.evaluate_trading_decision_as_trade_candidate_command import (
    EvaluateTradingDecisionAsTradeCandidateCommand,
)
from quantum.application.decision.results.trading_decision_command_result import (
    TradingDecisionCommandResult,
)
from quantum.application.shared.base_handlers.aggregate_command_handler import (
    AggregateCommandHandler,
)
from quantum.application.shared.eventing.application_event_context import (
    ApplicationEventContext,
)
from quantum.domain.decision.trading_decision.aggregate import TradingDecision
from quantum.domain.decision.trading_decision.states.trading_decision_state_base import (
    TradingDecisionStateBase,
)
from quantum.domain.shared_kernel.event_sourcing.events.base_event import BaseEvent
from quantum.domain.shared_kernel.modeling.identity.decision_id import DecisionId


class EvaluateTradingDecisionAsTradeCandidateHandler(
    AggregateCommandHandler[
        EvaluateTradingDecisionAsTradeCandidateCommand,
        TradingDecisionCommandResult,
        DecisionId,
        TradingDecisionStateBase,
        TradingDecision,
    ]
):
    """
    Use case: resolve a pending TradingDecision as a trade candidate.

    Existence policy expected at wiring:
    - MUST_EXIST
    """

    def _aggregate_id(
        self,
        command: EvaluateTradingDecisionAsTradeCandidateCommand,
    ) -> DecisionId:
        return command.decision_id

    def _context(
        self,
        command: EvaluateTradingDecisionAsTradeCandidateCommand,
    ) -> ApplicationEventContext:
        return command.context

    def _execute_domain(
        self,
        *,
        command: EvaluateTradingDecisionAsTradeCandidateCommand,
        aggregate: TradingDecision,
    ) -> tuple[Sequence[BaseEvent], TradingDecisionCommandResult]:
        events = aggregate.evaluate_as_trade_candidate(
            trade_direction=command.trade_direction,
        )

        return events, TradingDecisionCommandResult(decision_id=command.decision_id)
