from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Generic, TypeVar

from quantum.application.errors.application_error import DomainExecutionError
from quantum.application.ports.outbound.repositories.outbox_repository import (
    OutboxRepository,
)
from quantum.application.ports.outbound.unit_of_work import UnitOfWork
from quantum.application.services.event_enveloper import ApplicationEventEnveloper
from quantum.domain.shared_kernel.errors.domain_error import DomainError
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent

C = TypeVar("C")
R = TypeVar("R")


class ProcessCommandHandler(ABC, Generic[C, R]):
    """
    Stateless application-level orchestration handler.

    Guarantees:
    - No aggregate reconstruction
    - No event stream ownership
    - Deterministic transaction boundary
    - Outbox-only publication
    """

    def __init__(
        self,
        *,
        enveloper: ApplicationEventEnveloper,
        outbox: OutboxRepository,
        uow: UnitOfWork,
    ) -> None:
        self._enveloper = enveloper
        self._outbox = outbox
        self._uow = uow

    @abstractmethod
    def _execute_domain(self, *, command: C) -> tuple[Iterable[BaseEvent], R]:
        raise NotImplementedError

    def handle(self, command: C) -> R:
        with self._uow:
            try:
                domain_events, result = self._execute_domain(command=command)

                if domain_events:
                    envelopes = self._enveloper.envelope(events=domain_events)
                    self._outbox.add(envelopes)

                self._uow.commit()
                return result

            except DomainError as error:
                self._uow.rollback()
                raise DomainExecutionError(error) from None

            except Exception:
                self._uow.rollback()
                raise
