from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.modeling.value_objects.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class OrderCancellationReason(ClosedSetValueObject):
    """
    Canonical reason explaining WHY an order was cancelled.
    """

    @classmethod
    def _allowed_values(cls) -> frozenset[str]:
        return frozenset(
            {
                "user_requested",
                "strategy_decision",
                "risk_limit",
                "market_closed",
                "timeout",
                "broker_cancelled",
                "broker_rejected",
                "system_shutdown",
                "duplicate_order",
                "stale_order",
                "unknown",
            }
        )

    @classmethod
    def user_requested(cls) -> OrderCancellationReason:
        return cls("user_requested")

    @classmethod
    def strategy_decision(cls) -> OrderCancellationReason:
        return cls("strategy_decision")

    @classmethod
    def risk_limit(cls) -> OrderCancellationReason:
        return cls("risk_limit")

    @classmethod
    def timeout(cls) -> OrderCancellationReason:
        return cls("timeout")

    @classmethod
    def broker_cancelled(cls) -> OrderCancellationReason:
        return cls("broker_cancelled")

    @classmethod
    def broker_rejected(cls) -> OrderCancellationReason:
        return cls("broker_rejected")

    @classmethod
    def unknown(cls) -> OrderCancellationReason:
        return cls("unknown")
