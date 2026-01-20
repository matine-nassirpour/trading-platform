from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
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

    @classmethod
    def _allowed_values(cls) -> frozenset[str]:
        return frozenset(
            {
                "low",  # high uncertainty / fragile context
                "medium",  # standard operating conditions
                "high",  # strong conviction / stable regime
                "experimental",  # explicitly flagged experimental decision
            }
        )

    # --- Named constructors ---------------------------------------------------

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

    # --- Semantic helpers -----------------------------------------------------

    def is_high_confidence(self) -> bool:
        return self.value == "high"

    def is_low_confidence(self) -> bool:
        return self.value == "low"

    def is_experimental(self) -> bool:
        return self.value == "experimental"
