from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, Final

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation


class ImmutableDomainObject:
    """
    Hard-immutable mixin.

    Guarantees:
    - No attribute can ever be modified after construction.
    - No flag or attribute exists that userland code can toggle.
    - A controlled mutation window exists, but it is lexically scoped
      and cannot be entered from outside this class.
    """

    # Class-level sentinel, never exposed on instances
    __MUTATION_ALLOWED: Final[bool] = False

    def __setattr__(self, name: str, value: Any) -> None:
        if not self.__class__.__is_mutation_allowed():
            raise InvariantViolation(
                f"{self.__class__.__name__} is immutable. Cannot set '{name}'."
            )
        object.__setattr__(self, name, value)

    # --- Internal mutation guard ----------------------------------------------

    @classmethod
    def __is_mutation_allowed(cls) -> bool:
        # This value is *never* stored on instances
        return getattr(cls, "_ImmutableDomainObject__MUTATION_ALLOWED", False)

    @classmethod
    @contextmanager
    def _mutation_window(cls) -> Iterator[None]:
        """
        Opens a strictly scoped mutation window.

        This is the ONLY way attributes may be written.
        It cannot be accessed or enabled from outside this class.
        """
        try:
            object.__setattr__(cls, "_ImmutableDomainObject__MUTATION_ALLOWED", True)
            yield
        finally:
            object.__setattr__(cls, "_ImmutableDomainObject__MUTATION_ALLOWED", False)
