from __future__ import annotations

from typing import Final


class _StrictEnvironmentPolicy:
    """
    Immutable, safety-grade configuration for environment variable strictness.

    Guarantees:
        • Deterministic, global read-only policy
        • Suitable for safety-critical systems
        • No mutation allowed at runtime
    """

    __slots__ = ("_strict",)

    def __init__(self, strict: bool) -> None:
        self._strict: Final[bool] = strict

    @property
    def strict(self) -> bool:
        return self._strict


# Global read-only instance
STRICT_ENV_ROUTING: Final[_StrictEnvironmentPolicy] = _StrictEnvironmentPolicy(
    strict=True
)


def is_env_routing_strict() -> bool:
    """Public accessor for environment routing strictness."""
    return STRICT_ENV_ROUTING.strict
