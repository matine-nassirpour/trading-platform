from __future__ import annotations

import enum

from dataclasses import dataclass
from typing import Final

from quantum.domain.types.execution_channel import ExecutionChannel


class CircuitBreakerState(enum.Enum):
    """Finite state for a per-channel circuit breaker."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass(slots=True)
class CircuitBreakerConfig:
    """Configuration for circuit breaker behaviour.

    Attributes:
        failure_threshold: number of consecutive failures before opening.
        open_duration_s: minimum time to stay OPEN before probing.
        half_open_max_calls: number of trial calls allowed in HALF_OPEN.
    """

    failure_threshold: int = 3
    open_duration_s: float = 30.0
    half_open_max_calls: int = 5


@dataclass(slots=True)
class CircuitBreakerStateSnapshot:
    """Snapshot of a circuit breaker state for a given channel."""

    state: CircuitBreakerState
    consecutive_failures: int
    last_state_change_epoch_s: float
    half_open_trial_count: int


@dataclass(slots=True)
class ChannelStats:
    """Aggregated execution statistics for a single channel.

    This model deliberately uses simple aggregates to remain deterministic
    and auditable. More advanced models (e.g. sliding windows) can be built
    on top of this without breaking the API.
    """

    channel: ExecutionChannel
    total_requests: int = 0
    total_failures: int = 0
    total_successes: int = 0
    total_latency_ms: float = 0.0
    last_success_epoch_s: float | None = None
    last_failure_epoch_s: float | None = None

    def record_success(
        self, latency_ms: float | None, *, now_epoch_s: float
    ) -> ChannelStats:
        total_latency = self.total_latency_ms + (latency_ms or 0.0)
        return ChannelStats(
            channel=self.channel,
            total_requests=self.total_requests + 1,
            total_failures=self.total_failures,
            total_successes=self.total_successes + 1,
            total_latency_ms=total_latency,
            last_success_epoch_s=now_epoch_s,
            last_failure_epoch_s=self.last_failure_epoch_s,
        )

    def record_failure(
        self, latency_ms: float | None, *, now_epoch_s: float
    ) -> ChannelStats:
        total_latency = self.total_latency_ms + (latency_ms or 0.0)
        return ChannelStats(
            channel=self.channel,
            total_requests=self.total_requests + 1,
            total_failures=self.total_failures + 1,
            total_successes=self.total_successes,
            total_latency_ms=total_latency,
            last_success_epoch_s=self.last_success_epoch_s,
            last_failure_epoch_s=now_epoch_s,
        )

    @property
    def failure_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_failures / self.total_requests

    @property
    def average_latency_ms(self) -> float | None:
        if self.total_successes == 0:
            return None
        return self.total_latency_ms / max(1, self.total_successes)


@dataclass(slots=True)
class ChannelHealthScore:
    """Composite health score for a channel.

    Attributes:
        channel: execution channel.
        score: health score in [0, 100], where 100 is best.
        is_healthy: boolean flag for quick routing decisions.
        breaker_state: circuit breaker state for this channel.
        stats: last known stats snapshot (for observability).
    """

    channel: ExecutionChannel
    score: float
    is_healthy: bool
    breaker_state: CircuitBreakerState
    stats: ChannelStats


# Default thresholds to classify channels based on score
HEALTHY_SCORE_THRESHOLD: Final[float] = 70.0
DEGRADED_SCORE_THRESHOLD: Final[float] = 40.0
