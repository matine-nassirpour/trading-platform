from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.ddd.value_objects.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class DecisionSource(ClosedSetValueObject):
    """
    Describes HOW the trading decision was made.
    """

    @classmethod
    def _allowed_values(cls) -> frozenset[str]:
        return frozenset(
            {
                "systematic",  # fully automated model
                "discretionary",  # human decision
                "hybrid",  # human + model
                "risk_override",  # forced by risk engine
            }
        )

    # --- Named constructors ---------------------------------------------------

    @classmethod
    def systematic(cls) -> DecisionSource:
        return cls("systematic")

    @classmethod
    def discretionary(cls) -> DecisionSource:
        return cls("discretionary")

    @classmethod
    def hybrid(cls) -> DecisionSource:
        return cls("hybrid")

    @classmethod
    def risk_override(cls) -> DecisionSource:
        return cls("risk_override")
