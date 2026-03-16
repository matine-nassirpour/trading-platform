from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class CapitalReservationRejectionReasonCode(ClosedSetValueObject):
    """
    Stable, closed-set, machine-readable rejection reason codes.

    Required for:
    - audit
    - compliance
    - analytics
    - deterministic replay
    """

    @classmethod
    def _allowed_values(cls) -> frozenset[str]:
        return frozenset(
            {
                "insufficient_risk_budget",
                "capital_capacity_exhausted",
                "strategy_exposure_limit_reached",
                "portfolio_exposure_limit_reached",
                "reservation_policy_violation",
            }
        )

    # --- Named constructors ---------------------------------------------------

    @classmethod
    def insufficient_risk_budget(cls) -> CapitalReservationRejectionReasonCode:
        return cls("insufficient_risk_budget")

    @classmethod
    def capital_capacity_exhausted(cls) -> CapitalReservationRejectionReasonCode:
        return cls("capital_capacity_exhausted")

    @classmethod
    def strategy_exposure_limit_reached(
        cls,
    ) -> CapitalReservationRejectionReasonCode:
        return cls("strategy_exposure_limit_reached")

    @classmethod
    def portfolio_exposure_limit_reached(
        cls,
    ) -> CapitalReservationRejectionReasonCode:
        return cls("portfolio_exposure_limit_reached")

    @classmethod
    def reservation_policy_violation(
        cls,
    ) -> CapitalReservationRejectionReasonCode:
        return cls("reservation_policy_violation")
