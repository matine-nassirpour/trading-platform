from __future__ import annotations

from typing import Any

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation


class ImmutableDomainObject:
    """
    Mixin enforcing strict immutability after construction.
    """

    _IMMUTABLE = True

    def __setattr__(self, name: str, value: Any) -> None:
        if getattr(self, "_IMMUTABLE", False):
            raise InvariantViolation(
                f"{self.__class__.__name__} is immutable. Cannot set {name}."
            )
        object.__setattr__(self, name, value)
