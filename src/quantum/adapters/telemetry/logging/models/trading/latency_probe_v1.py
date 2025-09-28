from typing import Literal

from quantum.adapters.telemetry.logging.models.trading.base import BaseEvent


class LatencyProbeV1(BaseEvent):
    event_name: Literal["latency_probe_v1"] = "latency_probe_v1"
    app: Literal["ea_mql5", "python_core"]
    phase: Literal["terminal_ping", "order_check", "order_send", "ack", "fill"]
    symbol: str
    start_ms: int
    end_ms: int
