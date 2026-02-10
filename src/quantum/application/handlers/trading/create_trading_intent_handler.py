from quantum.application.commands.command_result import CommandResult
from quantum.application.commands.trading.create_trading_intent_command import (
    CreateTradingIntentCommand,
)
from quantum.application.handlers.base_handler import CommandHandler
from quantum.application.ports.outbound.event_store import EventStore
from quantum.domain.trading.intent.trading_intent import TradingIntent


class CreateTradingIntentHandler(CommandHandler[CreateTradingIntentCommand, None]):

    def __init__(self, event_store: EventStore, envelope_factory) -> None:
        self._event_store = event_store
        self._envelope_factory = envelope_factory

    def handle(self, command: CreateTradingIntentCommand):

        events = TradingIntent.create(
            intent_id=command.intent_id,
            symbol=command.symbol,
            side=command.side,
            decision_identity=command.decision_identity,
            context=command.context,
        )

        envelopes = [self._envelope_factory.wrap(e) for e in events]
        self._event_store.append(envelopes)

        return CommandResult()
