from collections.abc import Sequence

from quantum.application.decision.commands.evaluate_trading_decision_as_no_trade_command import (
    EvaluateTradingDecisionAsNoTradeCommand,
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


class EvaluateTradingDecisionAsNoTradeHandler(
    AggregateCommandHandler[
        EvaluateTradingDecisionAsNoTradeCommand,
        TradingDecisionCommandResult,
        DecisionId,
        TradingDecisionStateBase,
        TradingDecision,
    ]
):
    """
    Use case: resolve a pending TradingDecision as an explicit no-trade outcome.

    Existence policy expected at wiring:
    - MUST_EXIST
    """

    def _aggregate_id(
        self,
        command: EvaluateTradingDecisionAsNoTradeCommand,
    ) -> DecisionId:
        return command.decision_id

    def _context(
        self,
        command: EvaluateTradingDecisionAsNoTradeCommand,
    ) -> ApplicationEventContext:
        return command.context

    def _execute_domain(
        self,
        *,
        command: EvaluateTradingDecisionAsNoTradeCommand,
        aggregate: TradingDecision,
    ) -> tuple[Sequence[BaseEvent], TradingDecisionCommandResult]:
        events = aggregate.evaluate_as_no_trade(
            no_trade_decision=command.no_trade_decision,
        )

        return events, TradingDecisionCommandResult(decision_id=command.decision_id)
