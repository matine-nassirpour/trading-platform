from quantum.application.commands.command_result import CommandResult
from quantum.application.commands.trading.register_order_fill_command import (
    RegisterOrderFillCommand,
)
from quantum.application.handlers.base_handler import CommandHandler
from quantum.domain.trading.execution.order.order import Order


class RegisterOrderFillHandler(CommandHandler[RegisterOrderFillCommand, None]):

    def __init__(self, repository, event_store, envelope_factory):
        self._repository = repository
        self._event_store = event_store
        self._envelope_factory = envelope_factory

    def handle(self, command: RegisterOrderFillCommand):

        order: Order = self._repository.load(command.order_id)

        events = order.register_fill(fill=command.fill)

        envelopes = [self._envelope_factory.wrap(e) for e in events]
        self._event_store.append(envelopes)

        return CommandResult()
