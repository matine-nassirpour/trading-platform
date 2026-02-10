from quantum.application.commands.command_result import CommandResult
from quantum.application.commands.risk.trigger_killswitch_command import (
    TriggerKillSwitchCommand,
)
from quantum.application.errors.application_error import DomainExecutionError
from quantum.application.handlers.base_handler import CommandHandler
from quantum.application.ports.outbound.event_store import EventStore
from quantum.domain.risk.governance.aggregates.kill_switch.state import KillSwitchState


class TriggerKillSwitchHandler(CommandHandler[TriggerKillSwitchCommand, None]):

    def __init__(self, event_store: EventStore, repository, envelope_factory):
        self._event_store = event_store
        self._repository = repository
        self._envelope_factory = envelope_factory

    def handle(self, command: TriggerKillSwitchCommand) -> CommandResult[None]:

        try:
            aggregate: KillSwitchState = self._repository.load()

            events = aggregate.trigger(
                reason=command.reason,
                detail=command.detail,
            )

            envelopes = [self._envelope_factory.wrap(e) for e in events]

            self._event_store.append(envelopes)

            return CommandResult()

        except Exception as exc:
            raise DomainExecutionError(exc) from None
