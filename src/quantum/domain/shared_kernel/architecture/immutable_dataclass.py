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
    - slots=True
    - frozen=False (capability-based immutability only)
    - No dataclass-generated __setattr__ or __delattr__
    - Must inherit ImmutableDomainObject
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

    return decorated
