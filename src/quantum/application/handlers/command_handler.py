from typing import Generic, TypeVar

from quantum.application.commands.command_result import CommandResult
from quantum.application.ports.outbound.clock import Clock
from quantum.application.ports.outbound.event_bus_port import EventBusPort
from quantum.application.ports.outbound.event_store import EventStore
from quantum.application.ports.outbound.id_generator import IdGenerator
from quantum.application.ports.outbound.unit_of_work import UnitOfWork

C = TypeVar("C")
R = TypeVar("R")


class AsyncCommandHandler(Generic[C, R]):

    def __init__(
        self,
        *,
        uow: UnitOfWork,
        store: EventStore,
        bus: EventBusPort,
        clock: Clock,
        ids: IdGenerator,
    ) -> None:
        self._uow = uow
        self._store = store
        self._bus = bus
        self._clock = clock
        self._ids = ids

    async def handle(self, command: C) -> CommandResult[R]:
        raise NotImplementedError
