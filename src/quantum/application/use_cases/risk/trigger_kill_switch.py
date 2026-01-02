from quantum.application.dto.commands.trigger_kill_switch import (
    TriggerKillSwitchCommand,
)
from quantum.application.ports.aliases import EventPublisher, UoW


class TriggerKillSwitchUseCase:
    def __init__(self, *, repo, event_publisher: EventPublisher, uow: UoW) -> None:
        self._repo = repo
        self._event_publisher = event_publisher
        self._uow = uow

    def execute(self, command: TriggerKillSwitchCommand) -> None:
        with self._uow:
            state = self._repo.get_current()
            state = state.trigger(
                at=command.at,
                reason=command.reason,
                detail=command.detail,
            )

            self._repo.save(state)
            self._event_publisher.publish(state.events)
            self._uow.commit()
