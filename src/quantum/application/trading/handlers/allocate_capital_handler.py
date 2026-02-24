from collections.abc import Iterable

from quantum.application.shared.base_handlers.aggregate_command_handler import (
    AggregateCommandHandler,
)
from quantum.application.shared.base_handlers.aggregate_existence_policy import (
    AggregateExistencePolicy,
)
from quantum.application.trading.commands.allocate_capital_command import (
    AllocateCapitalCommand,
)
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent
from quantum.domain.trading.intent.trading_intent import TradingIntent


class AllocateCapitalHandler(
    AggregateCommandHandler[AllocateCapitalCommand, None, TradingIntent]
):

    def __init__(self, **kwargs):
        super().__init__(
            existence_policy=AggregateExistencePolicy.MUST_EXIST,
            **kwargs,
        )

    def _stream_id(self, command: AllocateCapitalCommand) -> str:
        return f"intent-{command.intent_id.value}"

    def _execute_domain(
        self,
        *,
        command: AllocateCapitalCommand,
        aggregate: TradingIntent,
    ) -> tuple[Iterable[BaseEvent], None]:

        events = aggregate.allocate_capital(
            allocation=command.allocation,
        )

        return events, None
