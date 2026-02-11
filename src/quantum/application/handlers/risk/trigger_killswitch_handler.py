from quantum.application.commands.command_result import CommandResult
from quantum.application.commands.risk.trigger_killswitch_command import (
    TriggerKillSwitchCommand,
)
from quantum.application.errors.application_error import DomainExecutionError
from quantum.application.handlers.command_handler import AsyncCommandHandler
from quantum.application.ports.outbound.clock import Clock
from quantum.application.ports.outbound.event_bus_port import EventBusPort
from quantum.application.ports.outbound.event_store import EventStore
from quantum.application.ports.outbound.id_generator import IdGenerator
from quantum.application.ports.outbound.unit_of_work import UnitOfWork
from quantum.application.services.event_pipeline import persist_and_publish
from quantum.domain.risk.governance.aggregates.kill_switch.state import KillSwitchState
from quantum.domain.shared_kernel.errors.domain_error import DomainError


class TriggerKillSwitchHandler(AsyncCommandHandler[TriggerKillSwitchCommand, None]):

    def __init__(
        self,
        uow: UnitOfWork,
        store: EventStore,
        bus: EventBusPort,
        clock: Clock,
        ids: IdGenerator,
    ) -> None:
        super().__init__(uow=uow, store=store, bus=bus, clock=clock, ids=ids)

    async def handle(self, command: TriggerKillSwitchCommand) -> CommandResult[None]:

        try:
            with self._uow:
                current_events = self._store.load_stream("killswitch")

                aggregate = KillSwitchState.rehydrate(
                    events=current_events,
                    empty_state=None,
                )

                domain_events = aggregate.trigger(
                    reason=command.reason,
                    detail=command.detail,
                )

                await persist_and_publish(
                    stream_id="killswitch",
                    events=domain_events,
                    store=self._store,
                    bus=self._bus,
                    ids=self._ids,
                    clock=self._clock,
                    actor="system:risk_engine",
                )

                self._uow.commit()

            return CommandResult()

        except DomainError as error:
            raise DomainExecutionError(error) from None
