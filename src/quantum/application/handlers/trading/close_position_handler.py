from quantum.application.commands.command_result import CommandResult
from quantum.application.commands.trading.close_position_command import (
    ClosePositionCommand,
)
from quantum.application.handlers.base_handler import CommandHandler
from quantum.domain.trading.execution.position.position import Position


class ClosePositionHandler(CommandHandler[ClosePositionCommand, None]):

    def __init__(self, repository, event_store, envelope_factory):
        self._repository = repository
        self._event_store = event_store
        self._envelope_factory = envelope_factory

    def handle(self, command: ClosePositionCommand):

        position: Position = self._repository.load(command.position_id)

        events = position.close(
            exit_price=command.exit_price,
            context=command.context,
        )

        envelopes = [self._envelope_factory.wrap(e) for e in events]
        self._event_store.append(envelopes)

        return CommandResult()
