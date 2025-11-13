from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from quantum.domain.types.execution_channel import ExecutionChannel


class BroadcastPolicy(Protocol):
    """
    Defines how broadcast executions are performed across channels.
    """

    def select_targets(
        self, available: Sequence[ExecutionChannel]
    ) -> Sequence[ExecutionChannel]:
        """Return the list of target channels for broadcast."""
        ...


class AllChannelsBroadcastPolicy(BroadcastPolicy):
    """Send to all available channels."""

    def select_targets(
        self, available: Sequence[ExecutionChannel]
    ) -> Sequence[ExecutionChannel]:
        return list(available)


class WeightedBroadcastPolicy(BroadcastPolicy):
    """Weighted allocation for proportional volume execution."""

    def __init__(self, weights: dict[ExecutionChannel, float]):
        self._weights = weights

    def select_targets(
        self, available: Sequence[ExecutionChannel]
    ) -> Sequence[ExecutionChannel]:
        return [c for c in available if c in self._weights and self._weights[c] > 0.0]

    def get_weight(self, channel: ExecutionChannel) -> float:
        return self._weights.get(channel, 0.0)
