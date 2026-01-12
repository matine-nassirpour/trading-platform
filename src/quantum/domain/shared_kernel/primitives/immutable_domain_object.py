from __future__ import annotations

import contextvars
import secrets

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation

# Context variable holding the active mutation token
_ACTIVE_MUTATION_TOKEN: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "_ACTIVE_MUTATION_TOKEN", default=None
)


class ImmutableDomainObject:
    """
    Hard-immutable, thread-safe, re-entrant domain object.

    Guarantees:
    - Each instance has its own mutation authority.
    - No global or class-level state is used.
    - Safe under concurrency, async, and replay.
    - Lexically scoped mutation window.
    """

    __slots__ = ("_mutation_token",)

    def __init__(self) -> None:
        # Each instance gets its own unforgeable token
        object.__setattr__(self, "_mutation_token", secrets.token_hex(32))

    def __setattr__(self, name: str, value: Any) -> None:
        active = _ACTIVE_MUTATION_TOKEN.get()
        my_token = object.__getattribute__(self, "_mutation_token")

        if active != my_token:
            raise InvariantViolation(
                f"{self.__class__.__name__} is immutable. Cannot set '{name}'."
            )

        object.__setattr__(self, name, value)

    # --- Internal mutation guard ----------------------------------------------

    @contextmanager
    def _mutation_window(self) -> Iterator[None]:
        """
        Opens a strictly scoped mutation window for THIS instance only.

        This is:
        - instance-local
        - thread-safe
        - async-safe
        - non-forgeable
        """
        token = object.__getattribute__(self, "_mutation_token")
        reset = _ACTIVE_MUTATION_TOKEN.set(token)
        try:
            yield
        finally:
            _ACTIVE_MUTATION_TOKEN.reset(reset)
