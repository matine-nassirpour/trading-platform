from quantum.application.commands.command_result import CommandResult
from quantum.application.commands.trading.authorize_trading_intent_command import (
    AuthorizeTradingIntentCommand,
)
from quantum.application.handlers.base_handler import CommandHandler
from quantum.domain.trading.intent.trading_intent import TradingIntent


class AuthorizeTradingIntentHandler(
    CommandHandler[AuthorizeTradingIntentCommand, None]
):

    def __init__(self, repository, event_store, envelope_factory):
        self._repository = repository
        self._event_store = event_store
        self._envelope_factory = envelope_factory

    def handle(self, command: AuthorizeTradingIntentCommand):

        intent: TradingIntent = self._repository.load(command.intent_id)

        events = intent.authorize(result=command.result)

        envelopes = [self._envelope_factory.wrap(e) for e in events]
        self._event_store.append(envelopes)

        return CommandResult()
