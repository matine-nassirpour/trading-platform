from __future__ import annotations

import dataclasses

from typing import TypeVar

from quantum.domain.shared_kernel.primitives.immutable_domain_object import (
    ImmutableDomainObject,
)

T = TypeVar("T")


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
    cls = dataclasses.dataclass(
        cls,
        frozen=False,  # CRITICAL: do NOT let dataclass override __setattr__
        eq=True,
        slots=True,
        repr=False,
    )

    # --- Hard guard: ensure we did not get a dataclass __setattr__
    if "__setattr__" in cls.__dict__:
        raise TypeError(
            f"{cls.__name__} illegally defines __setattr__ via dataclass. "
            "Use ImmutableDomainObject instead."
        )

    # --- Ensure class is immutable
    if not issubclass(cls, ImmutableDomainObject):
        raise TypeError(
            f"{cls.__name__} must inherit ImmutableDomainObject to be immutable"
        )

    return cls
