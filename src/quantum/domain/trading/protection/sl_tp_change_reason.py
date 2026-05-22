from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.modeling.value_objects.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class SlTpChangeReason(ClosedSetValueObject):
    """
    Canonical reason for a SL/TP configuration change.

    This describes WHY the protection envelope changed,
    not HOW it was computed.
    """

    @classmethod
    def _allowed_values(cls) -> frozenset[str]:
        return frozenset(
            {
                "initial",  # initial definition
                "manual",  # user / operator
                "strategy",  # systematic logic
                "risk",  # risk engine intervention
                "trailing",  # trailing stop logic
                "breakeven",  # breakeven logic
            }
        )

    # --- Named constructors ---------------------------------------------------

    @classmethod
    def initial(cls) -> SlTpChangeReason:
        return cls("initial")

    @classmethod
    def manual(cls) -> SlTpChangeReason:
        return cls("manual")

    @classmethod
    def strategy(cls) -> SlTpChangeReason:
        return cls("strategy")

    @classmethod
    def risk(cls) -> SlTpChangeReason:
        return cls("risk")

    @classmethod
    def trailing(cls) -> SlTpChangeReason:
        return cls("trailing")

    @classmethod
    def breakeven(cls) -> SlTpChangeReason:
        return cls("breakeven")
