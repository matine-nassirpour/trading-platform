from __future__ import annotations

import time

from collections.abc import Sequence
from dataclasses import dataclass

from quantum.domain.types.execution_channel import ExecutionChannel


@dataclass(frozen=True)
class ChannelHealth:
    channel: ExecutionChannel
    is_healthy: bool
    latency_ms: float | None = None
    last_check_epoch_s: float = time.time()


class HealthPolicy:
    """Tracks health of channels (latency, recent errors, heartbeat freshness)."""

    def __init__(self, ttl_s: float = 10.0) -> None:
        self._ttl_s = ttl_s
        self._states: dict[str, ChannelHealth] = {}

    def update_health(self, health: ChannelHealth) -> None:
        self._states[health.channel.value] = health

    def get_healthy_channels(
        self, all_channels: Sequence[ExecutionChannel]
    ) -> list[ExecutionChannel]:
        now = time.time()
        healthy = [
            c
            for c in all_channels
            if (state := self._states.get(c.value))
            and state.is_healthy
            and (now - state.last_check_epoch_s) < self._ttl_s
        ]
        return healthy or []
