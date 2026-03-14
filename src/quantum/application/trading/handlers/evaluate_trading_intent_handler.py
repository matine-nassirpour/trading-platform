from collections.abc import Iterable

from quantum.application.shared.base_handlers.aggregate_command_handler import (
    AggregateCommandHandler,
)
from quantum.application.shared.base_handlers.aggregate_existence_policy import (
    AggregateExistencePolicy,
)
from quantum.application.trading.commands.evaluate_trading_intent_command import (
    EvaluateTradingIntentCommand,
)
from quantum.domain.decision.intent.trading_intent import TradingIntent
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent


class EvaluateTradingIntentHandler(
    AggregateCommandHandler[EvaluateTradingIntentCommand, None, TradingIntent]
):

    def __init__(self, **kwargs):
        super().__init__(
            existence_policy=AggregateExistencePolicy.MUST_EXIST,
            **kwargs,
        )

    def _stream_id(self, command: EvaluateTradingIntentCommand) -> str:
        return f"intent-{command.intent_id.value}"

    def _execute_domain(
        self,
        *,
        command: EvaluateTradingIntentCommand,
        aggregate: TradingIntent,
    ) -> tuple[Iterable[BaseEvent], None]:

        domain_events = aggregate.evaluate(
            policy=command.policy,
            lifecycle=command.lifecycle,
            evaluated_at=command.evaluated_at,
        )

        return domain_events, None
