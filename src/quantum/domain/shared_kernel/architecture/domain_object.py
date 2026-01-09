from __future__ import annotations

from abc import ABC, abstractmethod

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole


class DomainObject(ABC):
    """
    Base class for every Domain class that participates in the architecture.
    """

    @classmethod
    @abstractmethod
    def role(cls) -> DomainRole:
        """
        Declares the architectural role of this class.
        Must be implemented.
        """
        raise NotImplementedError
