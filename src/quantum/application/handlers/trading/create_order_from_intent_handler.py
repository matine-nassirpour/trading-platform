from quantum.application.commands.command_result import CommandResult
from quantum.application.commands.trading.create_order_from_intent_command import (
    CreateOrderFromIntentCommand,
)
from quantum.application.errors.application_error import UseCaseError
from quantum.application.handlers.base_handler import CommandHandler
from quantum.domain.trading.execution.order.order import Order


class CreateOrderFromIntentHandler(CommandHandler[CreateOrderFromIntentCommand, None]):

    def __init__(self, intent_repository, event_store, envelope_factory):
        self._intent_repository = intent_repository
        self._event_store = event_store
        self._envelope_factory = envelope_factory

    def handle(self, command: CreateOrderFromIntentCommand):

        intent = self._intent_repository.load(command.intent_id)

        if not intent.state.authorized:
            raise UseCaseError("Intent not authorized")

        events = Order.create(
            intent_id=command.intent_id,
            order_id=command.order_id,
            symbol=intent.state.symbol,
            order_type=command.order_type,
            side=intent.state.side,
            volume=command.volume,
        )

        envelopes = [self._envelope_factory.wrap(e) for e in events]
        self._event_store.append(envelopes)

        return CommandResult()
