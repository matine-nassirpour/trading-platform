import inspect
import re

from abc import ABC
from dataclasses import dataclass, fields
from typing import ClassVar

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.structural_contract import (
    _assert_deep_immutability_of_instance_fields,
    _validate_structural_contract,
)

_EVENT_NAME_PATTERN = re.compile(r"^[a-z]+(\.[a-z0-9_]+)+$")
# Example: 'trading.order.created' or 'position.sl_tp.changed'

_FORBIDDEN_EVENT_FIELDS = frozenset(
    {
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
)


class EventDefinitionViolation(TypeError):
    """
    Raised when an event class violates the structural/event definition contract.
    """


@dataclass(frozen=True, slots=True)
class BaseEvent(ABC):
    """
    Canonical immutable Domain Event for an event-sourced domain model.

    HARD GUARANTEES:
    - Concrete subclasses must be dataclasses
    - Concrete subclasses must be frozen
    - Concrete subclasses must use slots
    - Concrete subclasses must not override __post_init__
    - Concrete subclasses must explicitly declare event_name
    - event_name must follow canonical naming convention
    - event_version must be an integer >= 1
    - Forbidden metadata fields must not appear in the domain payload
    - Payload values must be recursively immutable and deterministic

    NON-GOALS:
    - Recording metadata (event_id, occurred_at, stream_id, correlation_id, etc.)
      These belong to the event envelope / store record, not to the domain event itself.
    """

    event_name: ClassVar[str]
    event_version: ClassVar[int] = 1

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        if cls is BaseEvent:
            return

        if "__post_init__" in cls.__dict__:
            raise EventDefinitionViolation(
                f"{cls.__name__} must NOT override __post_init__. "
                "BaseEvent validation is final."
            )

        if inspect.isabstract(cls):
            return

        if "event_name" not in cls.__dict__:
            raise EventDefinitionViolation(
                f"{cls.__name__} must explicitly declare event_name"
            )

    def _validate_event_identity(self) -> None:
        if "event_name" not in self.__class__.__dict__:
            raise EventDefinitionViolation(
                f"{self.__class__.__name__} must explicitly declare event_name"
            )

        if not isinstance(self.event_name, str) or not self.event_name:
            raise InvariantViolation(
                f"{self.__class__.__name__}: event_name must be a non-empty string"
            )

        if not _EVENT_NAME_PATTERN.fullmatch(self.event_name):
            raise InvariantViolation(
                f"{self.__class__.__name__}: "
                f"event_name '{self.event_name}' does not match canonical format"
            )

        if not isinstance(self.event_version, int) or self.event_version < 1:
            raise InvariantViolation(
                f"{self.__class__.__name__}: event_version must be an integer >= 1"
            )

    def _validate_forbidden_fields(self) -> None:
        for f in fields(self):
            if f.name in _FORBIDDEN_EVENT_FIELDS:
                raise InvariantViolation(
                    f"{self.__class__.__name__} illegally defines forbidden field "
                    f"'{f.name}'"
                )

    def __post_init__(self) -> None:
        """
        FINAL.
        Must never be overridden by concrete event classes.
        """

        _validate_structural_contract(type(self))
        _assert_deep_immutability_of_instance_fields(self)
        self._validate_event_identity()
        self._validate_forbidden_fields()
