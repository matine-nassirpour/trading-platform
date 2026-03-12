from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from quantum.domain.shared_kernel.events.recorded_event_envelope import (
    RecordedEventEnvelope,
)
from quantum.domain.shared_kernel.projection.projection_cursor import ProjectionCursor

S = TypeVar("S")


class TransactionalProjectionRepository(ABC, Generic[S]):
    """
    Projection storage bound to UnitOfWork transaction.

    Guarantees:
    - Projection update occurs within same transaction as EventStore append.
    - Cursor monotonic enforcement.
    - Idempotency enforcement.
    """

    @abstractmethod
    def load(self) -> tuple[S, ProjectionCursor]:
        raise NotImplementedError

    @abstractmethod
    def save(
        self,
        *,
        state: S,
        cursor: ProjectionCursor,
        applied_events: list[RecordedEventEnvelope],
    ) -> None:
        """
        Save new projection state.

        Must enforce:
        - cursor monotonicity
        - no duplicate event application
        - transaction-bound persistence
        """
        raise NotImplementedError
