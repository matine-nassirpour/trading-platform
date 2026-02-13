from collections.abc import Iterable
from typing import Final

from quantum.application.commands.trading.authorize_trading_intent_command import (
    AuthorizeTradingIntentCommand,
)
from quantum.application.handlers.event_sourced_command_handler import (
    EventSourcedCommandHandler,
)
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent
from quantum.domain.trading.intent.trading_intent import TradingIntent


class AuthorizeTradingIntentHandler(
    EventSourcedCommandHandler[AuthorizeTradingIntentCommand, None, TradingIntent]
):
    """
    Authorizes a TradingIntent aggregate.
    """

    _ACTOR: Final[str] = "system:intent"

    def _stream_id(self, command: AuthorizeTradingIntentCommand) -> str:
        return f"intent-{command.intent_id.value}"

    def _execute_domain(
        self,
        *,
        command: AuthorizeTradingIntentCommand,
        aggregate: TradingIntent,
    ) -> tuple[Iterable[BaseEvent], None]:

        domain_events = aggregate.authorize(result=command.result)
        return domain_events, None
