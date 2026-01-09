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

    # --- Hard guard -----------------------------------------------------------

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        # Skip abstract base classes
        if getattr(cls, "__abstractmethods__", None):
            return

        # Enforce role declaration
        if "role" not in cls.__dict__:
            raise TypeError(
                f"{cls.__name__} must explicitly declare its DomainRole via role()"
            )

        role = cls.role()

        if not isinstance(role, DomainRole):
            raise TypeError(f"{cls.__name__}.role() must return a DomainRole")
