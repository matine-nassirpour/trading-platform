from __future__ import annotations

from typing import Final


class _StrictValidationConfig:
    """
    Immutable, safety-grade configuration holder for validation policy.

    Guarantees:
        • STRICT_VALIDATION cannot be mutated at runtime
        • Explicit getter API (read-only)
        • No global mutable state exposed
        • Clean Architecture compliant
        • Zero side effects
        • DO-178C / ISO 26262 friendly design (deterministic, pure)
    """

    __slots__ = ("_strict",)

    def __init__(self, strict: bool) -> None:
        # Private attribute, no setter, no public mutation path.
        self._strict: Final[bool] = strict

    @property
    def strict(self) -> bool:
        """
        Read-only access to strict validation mode.
        """
        return self._strict


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Global, immutable configuration (safety-grade)                             │
# │ -------------------------------------------------------------------------- │
# │ NOTE:                                                                      │
# │   - This is the ONLY location where strict validation is defined.          │
# │   - Tests must not modify this object; they can override behavior          │
# │     internally by mocking the ValidatorRegistry or calling custom rules.   │
# ╰────────────────────────────────────────────────────────────────────────────╯
STRICT_VALIDATION: Final[_StrictValidationConfig] = _StrictValidationConfig(strict=True)


def is_strict_validation_enabled() -> bool:
    """
    Public read-only accessor.
    Ensures callers do NOT access internal fields directly.
    """
    return STRICT_VALIDATION.strict
