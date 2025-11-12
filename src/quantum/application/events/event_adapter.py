"""
Event Adapter
─────────────
Adapts domain event objects into transport-ready payloads for EventBusPort.
This module performs no schema definition or validation.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def _event_name_of(event: object) -> str:
    if hasattr(event, "event_name"):
        name = event.event_name
        if isinstance(name, str) and name:
            return name
    # Fallback to class name if no explicit event_name
    return type(event).__name__


def _payload_of(event: object) -> dict[str, Any]:
    if hasattr(event, "to_payload") and callable(event.to_payload):
        payload = event.to_payload()
        if not isinstance(payload, Mapping):
            raise TypeError(f"to_payload() must return a mapping, got={type(payload)}")
        return dict(payload)

    # Fallback
    return {k: v for k, v in vars(event).items() if not k.startswith("_")}


def adapt_event_for_bus(event: object) -> tuple[str, dict[str, Any]]:
    """Return `(event_name, payload)` for a given domain event."""
    return _event_name_of(event), _payload_of(event)
