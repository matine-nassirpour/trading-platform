from __future__ import annotations

from collections.abc import Callable
from typing import Any


def get_gauge_value(gauge: Any) -> float:
    """Safely extract float value from a prometheus_client Gauge-like object."""
    value_attr: Any = getattr(gauge, "_value", None)
    getter: Callable[[], Any] | None = getattr(value_attr, "get", None)

    try:
        if callable(getter):
            value = getter()
            return float(value) if value is not None else -1.0
    except Exception:
        pass
    return -1.0
