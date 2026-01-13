from __future__ import annotations

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.architecture.immutable_dataclass import (
    immutable_dataclass,
)
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.mutation_key import MutationKey
from quantum.domain.shared_kernel.primitives.value_object import ValueObject


@immutable_dataclass
class EventSequence(ValueObject):
    """
    Strictly increasing, gapless sequence number within an event stream.

    Sequence 0 is RESERVED and means: 'before the first event'.
    """

    value: int

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.VALUE_OBJECT

    def _validate_semantics(self, key: MutationKey) -> None:
        if not isinstance(self.value, int):
            raise InvariantViolation("EventSequence must be an integer")

        if self.value < 0:
            raise InvariantViolation("EventSequence must be >= 0")

    @staticmethod
    def initial() -> EventSequence:
        return EventSequence(0)
