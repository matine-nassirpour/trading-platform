from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from quantum.domain.shared_kernel.identity.aggregate_id import AggregateId

ID = TypeVar("ID", bound=AggregateId)


class StreamNameResolver(ABC, Generic[ID]):
    """
    Application-facing abstraction responsible for deriving the storage
    stream name from a typed aggregate identity.

    This prevents leaking persistence naming conventions into handlers
    and preserves the domain/application identity continuity.
    """

    @abstractmethod
    def resolve(self, aggregate_id: ID) -> str:
        """
        Return the canonical event-stream name for the given aggregate id.
        """
        raise NotImplementedError
