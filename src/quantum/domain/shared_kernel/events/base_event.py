from abc import ABC
from dataclasses import dataclass, fields
from typing import ClassVar

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.structural_contract import (
    enforce_frozen_slot_dataclass_contract,
)

_FORBIDDEN_EVENT_FIELDS = {
    "id",
    "event_id",
    "timestamp",
    "occurred_at",
    "sequence",
    "version",
    "causation_id",
    "correlation_id",
    "stream_id",
}


@dataclass(frozen=True, slots=True)
class BaseEvent(ABC):
    """
    Canonical immutable Domain Event.

    A Domain Event represents:
    - WHAT happened
    - Not WHEN or WHERE it was recorded
    """

    event_name: ClassVar[str]
    event_version: ClassVar[int] = 1

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        if cls is BaseEvent:
            return

        enforce_frozen_slot_dataclass_contract(cls)

    def __post_init__(self) -> None:
        for f in fields(self):
            if f.name in _FORBIDDEN_EVENT_FIELDS:
                raise InvariantViolation(
                    f"{self.__class__.__name__} illegally defines forbidden field '{f.name}'"
                )
