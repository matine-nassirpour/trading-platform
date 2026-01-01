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
        "trading.v1.breakeven_trigger_event",
        "trading.v1.order_created_event",
        "trading.v1.order_intent_event",
        "trading.v1.order_sizing_event",
        "trading.v1.order_submit_event",
        "trading.v1.sl_tp_defined_event",
        "trading.v1.sl_tp_update_event",
        "trading.v1.trailing_trigger_event",
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
