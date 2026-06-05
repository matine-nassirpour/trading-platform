from collections.abc import Sequence

from quantum.application.decision.commands.create_trading_decision_command import (
    CreateTradingDecisionCommand,
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


class CreateTradingDecisionHandler(
    AggregateCommandHandler[
        CreateTradingDecisionCommand,
        TradingDecisionCommandResult,
        DecisionId,
        TradingDecisionStateBase,
        TradingDecision,
    ]
):
    """
    Use case: create a TradingDecision stream.

    Existence policy expected at wiring:
    - MUST_NOT_EXIST
    """

    def _aggregate_id(self, command: CreateTradingDecisionCommand) -> DecisionId:
        return command.decision_id

    def _context(
        self, command: CreateTradingDecisionCommand
    ) -> ApplicationEventContext:
        return command.context

    async def _execute_domain(
        self,
        *,
        command: CreateTradingDecisionCommand,
        aggregate: TradingDecision,
    ) -> tuple[Sequence[BaseEvent], TradingDecisionCommandResult]:
        _, events = TradingDecision.create_new(
            aggregate_id=command.decision_id,
            symbol=command.symbol,
            decision_qualification=command.decision_qualification,
            context=command.trading_context,
        )

        return events, TradingDecisionCommandResult(decision_id=command.decision_id)
