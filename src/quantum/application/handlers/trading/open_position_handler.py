from quantum.application.commands.command_result import CommandResult
from quantum.application.commands.trading.open_position_command import (
    OpenPositionCommand,
)
from quantum.application.handlers.base_handler import CommandHandler
from quantum.domain.trading.execution.position.position import Position


class OpenPositionHandler(CommandHandler[OpenPositionCommand, None]):

    def __init__(self, event_store, envelope_factory):
        self._event_store = event_store
        self._envelope_factory = envelope_factory

    def handle(self, command: OpenPositionCommand):

        events = Position.open(
            position_id=command.position_id,
            side=command.side,
            volume=command.volume,
            entry_price=command.entry_price,
        )

        envelopes = [self._envelope_factory.wrap(e) for e in events]
        self._event_store.append(envelopes)

        return CommandResult()
