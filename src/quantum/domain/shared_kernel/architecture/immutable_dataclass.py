from __future__ import annotations

import dataclasses

from typing import TypeVar

from quantum.domain.shared_kernel.primitives.construction_context import (
    construction_window,
)
from quantum.domain.shared_kernel.primitives.immutable_domain_object import (
    ImmutableDomainObject,
)

T = TypeVar("T", bound=type)

_IMMUTABLE_DATACLASS_MARKER = object()


def immutable_dataclass(cls: type[T]) -> type[T]:
    """
    Certified immutable dataclass for Domain Objects.

    HARD GUARANTEES:
    - slots=True
    - dataclass-generated __init__ runs inside a construction window
    - capability-based immutability is preserved
    - class is cryptographically (identity-wise) marked as immutable_dataclass
    """

    if not issubclass(cls, ImmutableDomainObject):
        raise TypeError(
            f"{cls.__name__} must inherit ImmutableDomainObject "
            "to use @immutable_dataclass"
        )

    # Apply dataclass with the ONLY allowed configuration
    decorated = dataclasses.dataclass(
        cls,
        slots=True,
        frozen=False,  # immutability is capability-based, NOT dataclass-based
        eq=True,
        repr=False,
    )

    params = dataclasses.dataclass_params(decorated)

    if params.frozen:
        raise TypeError(
            f"{cls.__name__} is frozen via dataclass — forbidden. "
            "Use capability-based immutability only."
        )

    if not params.slots:
        raise TypeError(
            f"{cls.__name__} must use slots=True for memory & safety guarantees."
        )

    decorated.__immutable_dataclass_marker__ = _IMMUTABLE_DATACLASS_MARKER

    # Capture the generated __init__
    original_init = decorated.__init__

    # Replace __init__ with one that opens a construction window
    def __init__(self, *args, **kwargs):
        with construction_window():
            original_init(self, *args, **kwargs)

    decorated.__init__ = __init__

    return decorated


# VERIFICATION API (used by ValueObject)


def is_immutable_dataclass(cls: type) -> bool:
    return (
        getattr(cls, "__immutable_dataclass_marker__", None)
        is _IMMUTABLE_DATACLASS_MARKER
    )
