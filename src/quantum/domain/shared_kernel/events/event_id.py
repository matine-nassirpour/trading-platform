from dataclasses import dataclass
from uuid import UUID

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation


@dataclass(frozen=True)
class EventId:
    """
    Globally unique, immutable event identifier.
    """

    value: UUID

    def __post_init__(self) -> None:
        if not isinstance(self.value, UUID):
            raise InvariantViolation("EventId must wrap a UUID")
