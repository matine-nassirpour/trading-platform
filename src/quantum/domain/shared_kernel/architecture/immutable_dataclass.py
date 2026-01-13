from __future__ import annotations

import dataclasses

from typing import TypeVar

from quantum.domain.shared_kernel.primitives.immutable_domain_object import (
    ImmutableDomainObject,
)

T = TypeVar("T", bound=type)


def immutable_dataclass(cls: type[T]) -> type[T]:
    """
    Certified immutable dataclass for Domain Objects.

    HARD GUARANTEES:
    - No dataclass-generated __setattr__
    - No dataclass-generated __delattr__
    - All immutability enforced by ImmutableDomainObject
    - __slots__ enforced
    """

    # --- Enforce slots for memory safety and immutability
    decorated: type[T] = dataclasses.dataclass(
        cls,
        frozen=False,  # immutability is capability-based, NOT dataclass-based
        eq=True,
        slots=True,
        repr=False,
    )

    # --- Hard architectural guard
    if not issubclass(cls, ImmutableDomainObject):
        raise TypeError(
            f"{cls.__name__} must inherit ImmutableDomainObject "
            "to use @immutable_dataclass"
        )

    # DO NOT wrap __post_init__
    # DO NOT delete _mutation_key
    # DO NOT create _mutation_key
    # That is the responsibility of the semantic base class.

    return decorated
