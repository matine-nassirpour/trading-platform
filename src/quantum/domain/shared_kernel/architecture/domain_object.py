from __future__ import annotations

import inspect

from abc import ABC, abstractmethod

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole


class DomainObject(ABC):
    """
    Root class for all domain-layer types governed by the Domain Charter.

    HARD GUARANTEE:
    - Every *concrete* domain class MUST explicitly declare its DomainRole.
    - Inherited roles are NOT allowed for concrete classes.
    - All domain objects support a controlled initialization window.
    """

    _INIT_FLAG = "_domain_initializing"

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

        # Skip abstract classes (they may define or inherit role)
        if inspect.isabstract(cls):
            return

        # Concrete class MUST declare role in its own namespace
        if "role" not in cls.__dict__:
            raise TypeError(
                f"{cls.__name__} must explicitly declare its DomainRole via role(). "
                f"Inherited roles are forbidden for concrete domain classes."
            )

        role = cls.role()

        if not isinstance(role, DomainRole):
            raise TypeError(
                f"{cls.__name__}.role() must return a DomainRole, got {type(role)}"
            )
