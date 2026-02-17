from collections.abc import Iterable

from quantum.application.shared.base_handlers.aggregate_command_handler import (
    AggregateCommandHandler,
)
from quantum.application.shared.base_handlers.aggregate_existence_policy import (
    AggregateExistencePolicy,
)
from quantum.application.trading.commands.authorize_trading_intent_command import (
    AuthorizeTradingIntentCommand,
)
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent
from quantum.domain.trading.intent.trading_intent import TradingIntent


class AuthorizeTradingIntentHandler(
    AggregateCommandHandler[AuthorizeTradingIntentCommand, None, TradingIntent]
):
    """
    Authorizes a TradingIntent aggregate.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(
            existence_policy=AggregateExistencePolicy.MUST_EXIST,
            **kwargs,
        )

    def _stream_id(self, command: AuthorizeTradingIntentCommand) -> str:
        return f"intent-{command.intent_id.value}"

    def _execute_domain(
        self,
        *,
        command: AuthorizeTradingIntentCommand,
        aggregate: TradingIntent | None,
    ) -> tuple[Iterable[BaseEvent], None]:

        if aggregate is None:
            raise RuntimeError(
                "TradingIntent aggregate missing despite MUST_EXIST policy enforcement."
            )

        domain_events = aggregate.authorize(result=command.result)
        return domain_events, None
