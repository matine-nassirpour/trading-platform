from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.modeling.value_objects.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class NoTradeReason(ClosedSetValueObject):
    """
    Canonical reason for a NO-TRADE decision.

    IMPORTANT:
    - This is NOT a failure
    - This is NOT an error
    - This is an EXPLICIT DECISION OUTCOME
    """

    @classmethod
    def _allowed_values(cls) -> frozenset[str]:
        return frozenset(
            {
                "no_signal",  # no actionable signal
                "regime_unfavorable",  # market regime not suitable
                "boundary_blocked",  # decision boundary veto
                "confidence_too_low",  # declared confidence insufficient
            }
        )

    # --- Named constructors ---------------------------------------------------

    @classmethod
    def no_signal(cls) -> NoTradeReason:
        return cls("no_signal")

    @classmethod
    def regime_unfavorable(cls) -> NoTradeReason:
        return cls("regime_unfavorable")

    @classmethod
    def boundary_blocked(cls) -> NoTradeReason:
        return cls("boundary_blocked")

    @classmethod
    def confidence_too_low(cls) -> NoTradeReason:
        return cls("confidence_too_low")
