from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.ddd.value_objects.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class CapitalReleaseReasonCode(ClosedSetValueObject):
    """
    Stable, closed-set, machine-readable release reason codes.

    Release is NOT rejection.
    It means previously reserved capital is no longer committed.
    """

    @classmethod
    def _allowed_values(cls) -> frozenset[str]:
        return frozenset(
            {
                "decision_cancelled",
                "reservation_expired",
                "execution_aborted",
                "manual_risk_intervention",
                "superseded",
            }
        )

    # --- Named constructors ---------------------------------------------------

    @classmethod
    def decision_cancelled(cls) -> CapitalReleaseReasonCode:
        return cls("decision_cancelled")

    @classmethod
    def reservation_expired(cls) -> CapitalReleaseReasonCode:
        return cls("reservation_expired")

    @classmethod
    def execution_aborted(cls) -> CapitalReleaseReasonCode:
        return cls("execution_aborted")

    @classmethod
    def manual_risk_intervention(cls) -> CapitalReleaseReasonCode:
        return cls("manual_risk_intervention")

    @classmethod
    def superseded(cls) -> CapitalReleaseReasonCode:
        return cls("superseded")
