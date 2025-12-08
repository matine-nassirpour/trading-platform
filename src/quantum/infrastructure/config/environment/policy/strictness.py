from __future__ import annotations

from typing import Final


class _StrictEnvironmentPolicy:
    """Immutable policy for environment strictness."""

    __slots__ = ("__strict",)

    def __init__(self, strict: bool) -> None:
        object.__setattr__(self, "_StrictEnvironmentPolicy__strict", strict)

    @property
    def strict(self) -> bool:
        return self.__strict

    def __setattr__(self, key, value) -> None:
        raise TypeError(f"{self.__class__.__name__} is immutable.")


# Global read-only instance (cannot be mutated or replaced)
STRICT_ENV_ROUTING: Final[_StrictEnvironmentPolicy] = _StrictEnvironmentPolicy(
    strict=True
)


def is_env_routing_strict() -> bool:
    """Public readonly accessor for environment routing strictness."""
    return STRICT_ENV_ROUTING.strict
