from typing import Protocol, runtime_checkable

from quantum.application.ports.outbound.transaction.unit_of_work import UnitOfWork


@runtime_checkable
class UnitOfWorkFactory(Protocol):
    """
    Factory for creating fresh UnitOfWork instances.

    Critical invariant:
    - Each call to create() must return a NEW, non-shared UnitOfWork.
    - UnitOfWork instances must never be reused across commands.
    - UnitOfWork instances must never be shared across concurrent tasks.
    """

    def create(self) -> UnitOfWork:
        raise NotImplementedError
