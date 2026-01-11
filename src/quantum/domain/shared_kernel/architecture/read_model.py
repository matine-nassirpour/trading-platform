from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any


class ReadModel(ABC):
    """
    Base contract for all read-side projection states.

    Read models are:
    - NOT part of the Domain
    - NOT governed by DomainRole
    - NOT allowed to contain business invariants
    - Pure data representations
    - Fully derived from domain events
    """

    @abstractmethod
    def identity(self) -> str:
        """
        Returns the stable identity of this read model.

        Used for:
        - Caching
        - UI routing
        - Snapshot storage
        - Idempotent updates
        """
        raise NotImplementedError

    @abstractmethod
    def as_dict(self) -> Mapping[str, Any]:
        """
        Returns a deterministic, JSON-serializable representation
        of this read model.

        Must contain no domain objects.
        """
        raise NotImplementedError
