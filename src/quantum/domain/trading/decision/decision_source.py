from __future__ import annotations

from typing import ClassVar

from quantum.domain.shared.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


class DecisionSource(ClosedSetValueObject):
    """
    Describes HOW the trading decision was made.
    """

    _ALLOWED_VALUES: ClassVar[frozenset[str]] = frozenset(
        {
            "systematic",  # fully automated model
            "discretionary",  # human decision
            "hybrid",  # human + model
            "risk_override",  # forced by risk engine
        }
    )

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
