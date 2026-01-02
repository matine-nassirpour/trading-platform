from __future__ import annotations

from typing import ClassVar

from quantum.domain.shared.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


class SlTpChangeReason(ClosedSetValueObject):
    """
    Canonical reason for a SL/TP configuration change.

    This describes WHY the protection envelope changed,
    not HOW it was computed.
    """

    _ALLOWED_VALUES: ClassVar[frozenset[str]] = frozenset(
        {
            "initial",  # initial definition
            "manual",  # user / operator
            "strategy",  # systematic logic
            "risk",  # risk engine intervention
            "trailing",  # trailing stop logic
            "breakeven",  # breakeven logic
        }
    )

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
