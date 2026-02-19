from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.primitives.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class DecisionAuthorizationReasonCode(ClosedSetValueObject):
    """
    Stable, closed-set, machine-readable reason codes.

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
                "strategy_not_authorized",
                "strategy_lifecycle_invalid",
                "market_regime_not_allowed",
                "policy_not_valid",
            }
        )

    @classmethod
    def strategy_not_authorized(cls) -> DecisionAuthorizationReasonCode:
        return cls("strategy_not_authorized")

    @classmethod
    def strategy_lifecycle_invalid(cls) -> DecisionAuthorizationReasonCode:
        return cls("strategy_lifecycle_invalid")

    @classmethod
    def market_regime_not_allowed(cls) -> DecisionAuthorizationReasonCode:
        return cls("market_regime_not_allowed")

    @classmethod
    def policy_not_valid(cls) -> DecisionAuthorizationReasonCode:
        return cls("policy_not_valid")
