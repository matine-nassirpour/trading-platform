from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.modeling.value_objects.closed_set_value_object import (
    ClosedSetValueObject,
)


@dataclass(frozen=True, slots=True)
class KillSwitchReason(ClosedSetValueObject):
    """
    Canonical machine-readable kill-switch trigger reason.

    This is a stable audit/compliance code, not a free-text explanation.
    """

    @classmethod
    def _allowed_values(cls) -> frozenset[str]:
        return frozenset(
            {
                # Risk governance
                "drawdown_limit",
                "daily_loss_limit",
                "exposure_limit",
                "notional_limit",
                "leverage_limit",
                "margin_limit",
                # Market safety
                "spread_anomaly",
                "liquidity_collapse",
                "volatility_spike",
                "market_closed",
                "news_event",
                # Execution / broker safety
                "broker_rejects",
                "broker_disconnect",
                "execution_latency",
                "order_desync",
                "fill_anomaly",
                # Infrastructure safety
                "network_disconnect",
                "data_feed_stale",
                "data_feed_corrupt",
                "clock_drift",
                "system_health",
                # Governance / human
                "compliance",
                "manual",
            }
        )

    # --- Risk governance ------------------------------------------------------

    @classmethod
    def drawdown_limit(cls) -> KillSwitchReason:
        return cls("drawdown_limit")

    @classmethod
    def daily_loss_limit(cls) -> KillSwitchReason:
        return cls("daily_loss_limit")

    @classmethod
    def exposure_limit(cls) -> KillSwitchReason:
        return cls("exposure_limit")

    @classmethod
    def notional_limit(cls) -> KillSwitchReason:
        return cls("notional_limit")

    @classmethod
    def leverage_limit(cls) -> KillSwitchReason:
        return cls("leverage_limit")

    @classmethod
    def margin_limit(cls) -> KillSwitchReason:
        return cls("margin_limit")

    # --- Market safety --------------------------------------------------------

    @classmethod
    def spread_anomaly(cls) -> KillSwitchReason:
        return cls("spread_anomaly")

    @classmethod
    def liquidity_collapse(cls) -> KillSwitchReason:
        return cls("liquidity_collapse")

    @classmethod
    def volatility_spike(cls) -> KillSwitchReason:
        return cls("volatility_spike")

    @classmethod
    def market_closed(cls) -> KillSwitchReason:
        return cls("market_closed")

    @classmethod
    def news_event(cls) -> KillSwitchReason:
        return cls("news_event")

    # --- Execution / broker safety -------------------------------------------

    @classmethod
    def broker_rejects(cls) -> KillSwitchReason:
        return cls("broker_rejects")

    @classmethod
    def broker_disconnect(cls) -> KillSwitchReason:
        return cls("broker_disconnect")

    @classmethod
    def execution_latency(cls) -> KillSwitchReason:
        return cls("execution_latency")

    @classmethod
    def order_desync(cls) -> KillSwitchReason:
        return cls("order_desync")

    @classmethod
    def fill_anomaly(cls) -> KillSwitchReason:
        return cls("fill_anomaly")

    # --- Infrastructure safety ------------------------------------------------

    @classmethod
    def network_disconnect(cls) -> KillSwitchReason:
        return cls("network_disconnect")

    @classmethod
    def data_feed_stale(cls) -> KillSwitchReason:
        return cls("data_feed_stale")

    @classmethod
    def data_feed_corrupt(cls) -> KillSwitchReason:
        return cls("data_feed_corrupt")

    @classmethod
    def clock_drift(cls) -> KillSwitchReason:
        return cls("clock_drift")

    @classmethod
    def system_health(cls) -> KillSwitchReason:
        return cls("system_health")

    # --- Governance / human ---------------------------------------------------

    @classmethod
    def compliance(cls) -> KillSwitchReason:
        return cls("compliance")

    @classmethod
    def manual(cls) -> KillSwitchReason:
        return cls("manual")

    # --- Semantic classifiers -------------------------------------------------

    def is_risk_governance_reason(self) -> bool:
        return self.value in {
            "drawdown_limit",
            "daily_loss_limit",
            "exposure_limit",
            "notional_limit",
            "leverage_limit",
            "margin_limit",
        }

    def is_market_safety_reason(self) -> bool:
        return self.value in {
            "spread_anomaly",
            "liquidity_collapse",
            "volatility_spike",
            "market_closed",
            "news_event",
        }

    def is_execution_safety_reason(self) -> bool:
        return self.value in {
            "broker_rejects",
            "broker_disconnect",
            "execution_latency",
            "order_desync",
            "fill_anomaly",
        }

    def is_infrastructure_safety_reason(self) -> bool:
        return self.value in {
            "network_disconnect",
            "data_feed_stale",
            "data_feed_corrupt",
            "clock_drift",
            "system_health",
        }

    def is_governance_reason(self) -> bool:
        return self.value in {
            "compliance",
            "manual",
        }
