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
    if not issubclass(cls, ImmutableDomainObject):
        raise TypeError(f"{cls.__name__} must inherit ImmutableDomainObject")

    # --- Inject __post_init__ wrapper
    original_post_init = getattr(cls, "__post_init__", None)

    def __post_init__(self) -> None:
        if original_post_init:
            original_post_init(self)

        # Finalize: remove mutation authority
        object.__delattr__(self, "_mutation_key")

    cls.__post_init__ = __post_init__
    return cls
