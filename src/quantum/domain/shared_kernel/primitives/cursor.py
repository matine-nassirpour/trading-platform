from __future__ import annotations

from abc import ABC, abstractmethod

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.architecture.domain_object import DomainObject
from quantum.domain.shared_kernel.architecture.immutable_dataclass import (
    immutable_dataclass,
)
from quantum.domain.shared_kernel.primitives.immutable_domain_object import (
    ImmutableDomainObject,
)


@immutable_dataclass
class Cursor(DomainObject, ImmutableDomainObject, ABC):
    """
    Canonical base class for all Domain Cursors.

    A Cursor:
    - Is NOT a ValueObject
    - Is NOT an Event
    - Is NOT an Entity

    It is a first-class architectural concept representing
    a monotonic, audit-grade position in a domain stream.
    """

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.CURSOR

    # --- Guard against misuse -------------------------------------------------

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

    # --- Validation pipeline --------------------------------------------------

    def __post_init__(self) -> None:
        with self._mutation_window():
            self._validate()

    @abstractmethod
    def _validate(self) -> None:
        """
        Enforces all cursor invariants.

        Must be deterministic, total, and side-effect free.
        """
        raise NotImplementedError
