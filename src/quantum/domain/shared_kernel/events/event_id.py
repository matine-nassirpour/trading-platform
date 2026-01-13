from __future__ import annotations

from uuid import UUID

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.architecture.immutable_dataclass import (
    immutable_dataclass,
)
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.mutation_key import MutationKey
from quantum.domain.shared_kernel.primitives.value_object import ValueObject

_NIL_UUID = UUID(int=0)


@immutable_dataclass
class EventId(ValueObject):
    """
    Globally unique, immutable event identifier.

    UUID(0) is reserved as the NIL event (before the first real event).
    """

    value: UUID

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.VALUE_OBJECT

    def _validate_semantics(self, key: MutationKey) -> None:
        if not isinstance(self.value, UUID):
            raise InvariantViolation("EventId must wrap a UUID")

    @staticmethod
    def nil() -> EventId:
        return EventId(_NIL_UUID)
