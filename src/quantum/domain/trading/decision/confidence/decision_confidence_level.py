from __future__ import annotations

from typing import ClassVar

from quantum.domain.shared_kernel.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


class DecisionConfidenceLevel(ClosedSetValueObject):
    """
    Canonical declared confidence level of a trading decision.

    IMPORTANT:
    - This is NOT a probability
    - This is NOT a score
    - This is NOT statistically meaningful
    - This is a GOVERNANCE SIGNAL

    Interpretation:
    - Used by risk, sizing, and control layers
    - Fully decoupled from model internals
    """

    _ALLOWED_VALUES: ClassVar[frozenset[str]] = frozenset(
        {
            "low",  # high uncertainty / fragile context
            "medium",  # standard operating conditions
            "high",  # strong conviction / stable regime
            "experimental",  # explicitly flagged experimental decision
        }
    )

    # --- Named constructors --------------------------------------------------

    @classmethod
    def low(cls) -> DecisionConfidenceLevel:
        return cls("low")

    @classmethod
    def medium(cls) -> DecisionConfidenceLevel:
        return cls("medium")

    @classmethod
    def high(cls) -> DecisionConfidenceLevel:
        return cls("high")

    @classmethod
    def experimental(cls) -> DecisionConfidenceLevel:
        return cls("experimental")

    # --- Semantic helpers ----------------------------------------------------

    def is_high_confidence(self) -> bool:
        return self.value == "high"

    def is_low_confidence(self) -> bool:
        return self.value == "low"

    def is_experimental(self) -> bool:
        return self.value == "experimental"
