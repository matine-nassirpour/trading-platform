from typing import Final

from quantum.application.commands.trading.close_position_command import (
    ClosePositionCommand,
)
from quantum.application.errors.application_error import DomainExecutionError
from quantum.application.handlers.command_handler import CommandHandler
from quantum.application.ports.outbound.clock import Clock
from quantum.application.ports.outbound.event_store import EventStore
from quantum.application.ports.outbound.id_generator import IdGenerator
from quantum.application.ports.outbound.outbox_repository import OutboxRepository
from quantum.application.ports.outbound.repositories.position_repository import (
    PositionRepository,
)
from quantum.application.ports.outbound.unit_of_work import UnitOfWork
from quantum.application.services.event_pipeline import persist_events_transactionally
from quantum.domain.shared_kernel.errors.domain_error import DomainError
from quantum.domain.shared_kernel.events.event_sequence import EventSequence


class ClosePositionHandler(CommandHandler[ClosePositionCommand, None]):
    """
    Closes an existing Position aggregate.
    """

    _ACTOR: Final[str] = "system:position"

    def __init__(
        self,
        *,
        position_repository: PositionRepository,
        outbox: OutboxRepository,
        uow: UnitOfWork,
        store: EventStore,
        clock: Clock,
        ids: IdGenerator,
    ) -> None:
        super().__init__(outbox=outbox, uow=uow, store=store, clock=clock, ids=ids)
        self._position_repository = position_repository

    def _execute(self, command: ClosePositionCommand) -> None:

        try:
            stream_id = f"position-{command.position_id.value}"

            # --- Optimistic concurrency guard
            current_version: EventSequence = self._store.current_sequence(stream_id)

            position = self._position_repository.load(command.position_id)

            # --- Domain logic
            domain_events = position.close(
                exit_price=command.exit_price,
                context=command.context,
            )

            # --- Transactional persistence (EventStore + Outbox)
            persist_events_transactionally(
                stream_id=stream_id,
                events=domain_events,
                store=self._store,
                outbox=self._outbox,
                uow=self._uow,
                ids=self._ids,
                clock=self._clock,
                actor=self._ACTOR,
                expected_version=current_version,
            )

        except DomainError as error:
            raise DomainExecutionError(error) from None
