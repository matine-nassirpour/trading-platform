from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from typing import Any, ClassVar, Self

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.shared_kernel.events.handler_registry import build_handler_registry
from quantum.domain.shared_kernel.primitives.aggregate_lifecycle import (
    AggregateLifecycle,
)
from quantum.domain.shared_kernel.primitives.aggregate_state import AggregateState
from quantum.domain.shared_kernel.primitives.mutable_aggregate_root import (
    MutableAggregateRoot,
)
from quantum.domain.shared_kernel.primitives.validatable_aggregate import (
    ValidatableAggregate,
)

EventKey = tuple[str, int]  # (event_name, event_version)


class EventSourcedAggregateRoot(
    AggregateLifecycle,
    MutableAggregateRoot,
    ValidatableAggregate,
):
    """
    Canonical base class for Event-Sourced Aggregates.

    HARD GUARANTEES:
    - Only BaseEvent instances may ever be applied
    - All state changes happen via domain events
    - No direct aggregate attribute mutation is allowed
    - Aggregate invariants validated after every new event
    - Replay is deterministic and free of subclass side effects
    - State is declarative & audit-grade (typed, slots-only)
    - Event handlers are isolated per Aggregate class
    """

    __slots__ = ("_state",)

    _EVENT_HANDLERS: ClassVar[Mapping[EventKey, Callable]]
    _STATE_TYPE: ClassVar[type[AggregateState]]

    # --- Domain role ----------------------------------------------------------

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.AGGREGATE

    # --- Class construction ---------------------------------------------------

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        # Enforce presence and validity of _STATE_TYPE on concrete aggregates.
        # (Abstract aggregates may intentionally omit it.)
        if not getattr(cls, "__abstractmethods__", None):
            # Not perfectly reliable for all ABC patterns; still a strong guard.
            if not hasattr(cls, "_STATE_TYPE"):
                raise TypeError(
                    f"{cls.__name__} must define _STATE_TYPE: type[AggregateState]"
                )

            state_type = cls._STATE_TYPE
            if not isinstance(state_type, type) or not issubclass(
                state_type, AggregateState
            ):
                raise TypeError(
                    f"{cls.__name__}._STATE_TYPE must be a subclass of AggregateState"
                )

            state_type._assert_valid_state_type()

        # Compile and freeze the handler registry
        cls._EVENT_HANDLERS = build_handler_registry(cls)

    # --- Lifecycle ------------------------------------------------------------

    def __init__(self) -> None:
        """
        Live constructor. Must remain side-effect free.

        IMPORTANT:
        - Subclasses SHOULD NOT override __init__.
        - If they do, it must be parameterless and side-effect free.
        """
        super().__init__()
        object.__setattr__(self, "_state", self._STATE_TYPE())

    # --- Attribute access -----------------------------------------------------

    def __getattr__(self, name: str) -> Any:
        state = object.__getattribute__(self, "_state")
        if hasattr(state, name):
            return getattr(state, name)
        raise AttributeError(name)

    # --- Controlled mutation API (used only by engine) ------------------------

    def _mutate(self, field: str, value: Any) -> None:
        """
        Writes into the protected typed state capsule.

        HARD GUARANTEES:
        - Only callable inside an authorized mutation window
        - Only declared fields may be mutated (audit-grade)
        """
        self._assert_mutating()

        state = object.__getattribute__(self, "_state")
        if not hasattr(state, field):
            raise InvariantViolation(
                f"{self.__class__.__name__}: unknown state field '{field}'. "
                "All state fields must be declared in the AggregateState __slots__."
            )

        object.__setattr__(state, field, value)

    # --- Event handling -------------------------------------------------------

    def _raise(self, event: BaseEvent) -> BaseEvent:
        """
        Applies a new domain event and validates invariants.
        """
        self._apply(event)
        self._validate_state()
        return event

    def _apply(self, event: BaseEvent) -> None:
        """
        Applies a single domain event inside a mutation-safe window.
        """
        if not isinstance(event, BaseEvent):
            raise InvariantViolation(
                f"{self.__class__.__name__} can only apply BaseEvent, "
                f"got {type(event).__name__}"
            )

        key = (event.event_name, event.event_version)

        handlers = self.__class__._EVENT_HANDLERS
        if key not in handlers:
            raise InvariantViolation(
                f"{self.__class__.__name__} cannot apply event {key}"
            )

        handler = handlers[key]

        with self._mutation_window():
            handler(self, event)

    # --- Replay ---------------------------------------------------------------

    @classmethod
    def rehydrate(cls, events: Iterable[BaseEvent]) -> Self:
        """
        Rebuilds an aggregate from its event stream.

        HARD GUARANTEES:
        - Does NOT call subclass __init__
        - Initializes engine internals only
        - Deterministic, replay-safe
        """
        # Create instance without __init__
        instance = cls._empty()

        # Initialize mutation guard / DomainObject bases (no side effects)
        # MutableAggregateRoot has a trivial __init__ but we call it explicitly
        # to preserve MRO expectations.
        MutableAggregateRoot.__init__(instance)

        # Initialize typed state deterministically
        object.__setattr__(instance, "_state", cls._STATE_TYPE())

        # Apply events deterministically
        for event in events:
            instance._apply(event)

        # Validate invariants after full replay
        instance._validate_state()
        return instance

    # --- Contracts ------------------------------------------------------------

    def _validate_state(self) -> None:
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _validate_state()"
        )
