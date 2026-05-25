from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.modeling.value_objects.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class PositionSizingRejectionReasonCode(ClosedSetValueObject):
    """
    Stable machine-readable sizing rejection reason codes.
    """

    @classmethod
    def _allowed_values(cls) -> frozenset[str]:
        return frozenset(
            {
                "non_positive_equity",
                "invalid_stop_distance",
                "stop_distance_below_broker_minimum",
                "risk_amount_too_small",
                "volume_below_minimum",
                "volume_above_maximum",
                "volume_not_step_aligned",
                "notional_capacity_exhausted",
                "sizing_policy_violation",
            }
        )

    @classmethod
    def non_positive_equity(cls) -> PositionSizingRejectionReasonCode:
        return cls("non_positive_equity")

    @classmethod
    def invalid_stop_distance(cls) -> PositionSizingRejectionReasonCode:
        return cls("invalid_stop_distance")

    @classmethod
    def stop_distance_below_broker_minimum(cls) -> PositionSizingRejectionReasonCode:
        return cls("stop_distance_below_broker_minimum")

    @classmethod
    def risk_amount_too_small(cls) -> PositionSizingRejectionReasonCode:
        return cls("risk_amount_too_small")

    @classmethod
    def volume_below_minimum(cls) -> PositionSizingRejectionReasonCode:
        return cls("volume_below_minimum")

    @classmethod
    def volume_above_maximum(cls) -> PositionSizingRejectionReasonCode:
        return cls("volume_above_maximum")

    @classmethod
    def volume_not_step_aligned(cls) -> PositionSizingRejectionReasonCode:
        return cls("volume_not_step_aligned")

    @classmethod
    def notional_capacity_exhausted(cls) -> PositionSizingRejectionReasonCode:
        return cls("notional_capacity_exhausted")

    @classmethod
    def sizing_policy_violation(cls) -> PositionSizingRejectionReasonCode:
        return cls("sizing_policy_violation")
