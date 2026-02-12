from typing import Final

from quantum.application.commands.decision.register_no_trade_command import (
    RegisterNoTradeCommand,
)
from quantum.application.errors.application_error import DomainExecutionError
from quantum.application.handlers.command_handler import CommandHandler
from quantum.application.ports.outbound.clock import Clock
from quantum.application.ports.outbound.event_store import EventStore
from quantum.application.ports.outbound.id_generator import IdGenerator
from quantum.application.ports.outbound.outbox_repository import OutboxRepository
from quantum.application.ports.outbound.unit_of_work import UnitOfWork
from quantum.application.services.event_pipeline import persist_events_transactionally
from quantum.domain.decision.events.v1.no_trade_decision_event import (
    NoTradeDecisionEvent,
)
from quantum.domain.shared_kernel.errors.domain_error import DomainError
from quantum.domain.shared_kernel.events.event_sequence import EventSequence


class RegisterNoTradeHandler(CommandHandler[RegisterNoTradeCommand, None]):
    """
    Registers a No-Trade decision in a strictly transactional,
    event-sourced and concurrency-safe manner.
    """

    _ACTOR: Final[str] = "system:decision_engine"

    def __init__(
        self,
        *,
        outbox: OutboxRepository,
        uow: UnitOfWork,
        store: EventStore,
        clock: Clock,
        ids: IdGenerator,
    ) -> None:
        super().__init__(outbox=outbox, uow=uow, store=store, clock=clock, ids=ids)

    def _execute(self, command: RegisterNoTradeCommand) -> None:

        try:
            stream_id = f"decision-{command.decision_identity.strategy_id.value}"

            # --- Optimistic concurrency guard
            current_version: EventSequence = self._store.current_sequence(stream_id)

            # --- Domain event construction
            domain_events = [
                NoTradeDecisionEvent(
                    symbol=command.symbol,
                    decision_identity=command.decision_identity,
                    no_trade_decision=command.outcome,
                )
            ]

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
