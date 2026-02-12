from typing import Final

from quantum.application.commands.risk.register_pnl_command import RegisterPnLCommand
from quantum.application.errors.application_error import DomainExecutionError
from quantum.application.handlers.command_handler import CommandHandler
from quantum.application.ports.outbound.clock import Clock
from quantum.application.ports.outbound.event_store import EventStore
from quantum.application.ports.outbound.id_generator import IdGenerator
from quantum.application.ports.outbound.outbox_repository import OutboxRepository
from quantum.application.ports.outbound.repositories.risk_repository import (
    RiskRepository,
)
from quantum.application.ports.outbound.unit_of_work import UnitOfWork
from quantum.application.services.event_pipeline import persist_events_transactionally
from quantum.domain.shared_kernel.errors.domain_error import DomainError
from quantum.domain.shared_kernel.events.event_sequence import EventSequence


class RegisterPnLHandler(CommandHandler[RegisterPnLCommand, None]):
    """
    Registers realized PnL and updates global risk state.
    """

    _ACTOR: Final[str] = "system:risk_engine"

    def __init__(
        self,
        *,
        risk_repository: RiskRepository,
        outbox: OutboxRepository,
        uow: UnitOfWork,
        store: EventStore,
        clock: Clock,
        ids: IdGenerator,
    ) -> None:
        super().__init__(outbox=outbox, uow=uow, store=store, clock=clock, ids=ids)
        self._risk_repository = risk_repository

    def _execute(self, command: RegisterPnLCommand) -> None:

        try:
            stream_id = "risk-state"

            # --- Optimistic concurrency guard
            current_version: EventSequence = self._store.current_sequence(stream_id)

            aggregate = self._risk_repository.load()

            # --- Domain logic
            domain_events = aggregate.register_pnl(
                pnl=command.pnl,
                drawdown=command.drawdown,
                daily_loss=command.daily_loss,
                exposure=command.exposure,
                notional=command.notional,
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
