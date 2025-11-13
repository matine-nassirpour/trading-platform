"""
Event Topic Mapping
───────────────────
Deterministic mapping from event_name → bus topic.

This indirection:
- decouples domain naming from transport topics,
- enables clean governance & ACLs per topic,
- supports stable contracts for downstream consumers.

Adjust mappings to your org conventions (e.g. Kafka topics).
"""

from __future__ import annotations


def map_topic(event_name: str) -> str:
    # Trading lifecycle (always business topics)
    if event_name in {
        "trading.v1.order_intent",
        "trading.v1.order_submit",
        "trading.v1.order_check",
        "trading.v1.order_fill",
        "trading.v1.order_reject",
        "trading.v1.position_update",
        "trading.v1.sl_tp_update",
        "trading.v1.stoploss_trigger",
        "trading.v1.takeprofit_trigger",
        "trading.v1.trailing_trigger",
        "trading.v1.breakeven_trigger",
        "trading.v1.killswitch_trigger",
        "trading.v1.reconciliation",
    }:
        return "trading.events"

    # Health / diagnostics that still needed on the bus
    if event_name in {"trading.v1.mt5_health", "system.execution_channel"}:
        return "system.health"

    # Low-level telemetry
    if event_name in {"trading.v1.order_ack", "trading.v1.latency_probe"}:
        return "system.telemetry"

    # Default: conservative business topic
    return "trading.events"
