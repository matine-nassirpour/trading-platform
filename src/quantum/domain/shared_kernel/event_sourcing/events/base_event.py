import inspect
import re

from abc import ABC
from dataclasses import dataclass, fields
from typing import ClassVar, final

from quantum.domain.shared_kernel.foundation.bases.canonical_domain_state_object import (
    CanonicalDomainStateObject,
)
from quantum.domain.shared_kernel.foundation.contracts.violations import (
    StructuralContractViolation,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation

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
        "aggregate_id",
        "recorded_at",
        "metadata",
    }
)


@dataclass(frozen=True, slots=True)
class BaseEvent(CanonicalDomainStateObject, ABC):
    """
    Canonical immutable Domain Event for an event-sourced domain model.

    GUARANTEES:
    - Concrete subclasses must be dataclasses
    - Concrete subclasses must be frozen
    - Concrete subclasses must use slots
    - Concrete subclasses must NOT override __post_init__
    - Concrete subclasses must NOT override _validate()
    - Concrete subclasses must explicitly declare event_name
    - event_name must follow canonical naming convention
    - event_version must be an integer >= 1
    - Forbidden envelope/record metadata fields must not appear in the payload
    - Payload values must be recursively immutable and deterministic
    - Semantic payload validation is extensible via _validate_payload()

    NON-GOALS:
    - Recording metadata belongs to the envelope / event record, not to the event payload.
    """

    event_name: ClassVar[str]
    event_version: ClassVar[int] = 1

    # --- Internal Helpers -----------------------------------------------------

    @classmethod
    def _assert_class_level_event_identity_definition(cls) -> None:
        event_name = cls.__dict__.get("event_name")
        if not isinstance(event_name, str) or not event_name:
            raise StructuralContractViolation(
                f"{cls.__name__}.event_name must be a non-empty string."
            )

        if not _EVENT_NAME_PATTERN.fullmatch(event_name):
            raise StructuralContractViolation(
                f"{cls.__name__}.event_name must match canonical format "
                f"{_EVENT_NAME_PATTERN.pattern!r}, got {event_name!r}."
            )

        event_version = cls.__dict__.get(
            "event_version", getattr(cls, "event_version", 1)
        )
        if not isinstance(event_version, int) or event_version < 1:
            raise StructuralContractViolation(
                f"{cls.__name__}.event_version must be an integer >= 1."
            )

    def _validate_event_identity_at_runtime(self) -> None:
        if "event_name" not in self.__class__.__dict__:
            raise StructuralContractViolation(
                f"{self.__class__.__name__} must explicitly declare event_name"
            )

        if not isinstance(self.event_name, str) or not self.event_name:
            raise InvariantViolation(
                f"{self.__class__.__name__}: event_name must be a non-empty string"
            )

        if not _EVENT_NAME_PATTERN.fullmatch(self.event_name):
            raise InvariantViolation(
                f"{self.__class__.__name__}: "
                f"event_name {self.event_name!r} does not match canonical format"
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
                    f"{f.name!r}"
                )

    # --- Class creation enforcement -------------------------------------------

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        if cls is BaseEvent:
            return

        if "_validate_semantics" in cls.__dict__:
            raise StructuralContractViolation(
                f"{cls.__name__} must NOT override _validate_semantics(). "
                "Use _validate_payload() instead."
            )

        if inspect.isabstract(cls):
            return

        if "event_name" not in cls.__dict__:
            raise StructuralContractViolation(
                f"{cls.__name__} must explicitly declare event_name"
            )

        cls._assert_class_level_event_identity_definition()

    # --- Construction Guarantee -----------------------------------------------

    def _validate_payload(self) -> None:
        """
        Semantic payload validation hook for concrete domain events.
        """
        return None

    @final
    def _validate_semantics(self) -> None:
        """
        FINAL validation pipeline.

        This method is intentionally non-overridable.
        Concrete subclasses must extend event validation only through
        _validate_payload().
        """
        self._validate_event_identity_at_runtime()
        self._validate_forbidden_fields()
        self._validate_payload()
