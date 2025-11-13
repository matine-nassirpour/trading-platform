from __future__ import annotations

import asyncio
import time

from collections.abc import Sequence

from quantum.domain.types.execution_channel import ExecutionChannel

from .circuit_breaker import CircuitBreaker
from .health_model import (
    DEGRADED_SCORE_THRESHOLD,
    HEALTHY_SCORE_THRESHOLD,
    ChannelHealthScore,
    ChannelStats,
    CircuitBreakerState,
    CircuitBreakerStateSnapshot,
)


class HealthService:
    """Centralized health evaluation for execution channels.

    This service combines:
        - lightweight aggregated statistics per channel,
        - a per-channel circuit breaker,
        - a composite health score suitable for routing decisions.

    It is designed to be:
        - async-friendly (single asyncio.Lock),
        - deterministic and auditable,
        - easily extensible without breaking external contracts.
    """

    def __init__(
        self,
        *,
        circuit_breaker: CircuitBreaker,
        stats_ttl_s: float = 60.0,
    ) -> None:
        self._circuit_breaker = circuit_breaker
        self._stats_ttl_s = stats_ttl_s
        self._stats: dict[str, ChannelStats] = {}
        self._lock = asyncio.Lock()

    async def record_success(
        self,
        channel: ExecutionChannel,
        *,
        latency_ms: float | None,
    ) -> ChannelHealthScore:
        """Record a successful execution and update health metrics."""
        now = time.time()
        key = channel.value

        async with self._lock:
            stats = self._stats.get(key) or ChannelStats(channel=channel)
            stats = stats.record_success(latency_ms=latency_ms, now_epoch_s=now)
            self._stats[key] = stats

            breaker_snapshot = self._circuit_breaker.on_success(key)
            score = self._compute_score(stats, breaker_snapshot)

        return ChannelHealthScore(
            channel=channel,
            score=score,
            is_healthy=score >= HEALTHY_SCORE_THRESHOLD,
            breaker_state=breaker_snapshot.state,
            stats=stats,
        )

    async def record_failure(
        self,
        channel: ExecutionChannel,
        *,
        latency_ms: float | None,
    ) -> ChannelHealthScore:
        """Record a failed execution and update health metrics."""
        now = time.time()
        key = channel.value

        async with self._lock:
            stats = self._stats.get(key) or ChannelStats(channel=channel)
            stats = stats.record_failure(latency_ms=latency_ms, now_epoch_s=now)
            self._stats[key] = stats

            breaker_snapshot = self._circuit_breaker.on_failure(key)
            score = self._compute_score(stats, breaker_snapshot)

        return ChannelHealthScore(
            channel=channel,
            score=score,
            is_healthy=score >= HEALTHY_SCORE_THRESHOLD,
            breaker_state=breaker_snapshot.state,
            stats=stats,
        )

    async def get_health_score(
        self,
        channel: ExecutionChannel,
    ) -> ChannelHealthScore | None:
        """Return the last known health score for a channel, if any."""
        key = channel.value
        now = time.time()

        async with self._lock:
            stats = self._stats.get(key)
            if stats is None:
                return None

            # TTL-based expiry for stale stats
            last_ts = stats.last_success_epoch_s or stats.last_failure_epoch_s
            if last_ts is not None and (now - last_ts) > self._stats_ttl_s:
                # Consider the stats stale; drop them and rely on breaker state
                del self._stats[key]
                stats = ChannelStats(channel=channel)

            breaker_snapshot = self._circuit_breaker.can_attempt(key)
            score = self._compute_score(stats, breaker_snapshot)

        return ChannelHealthScore(
            channel=channel,
            score=score,
            is_healthy=score >= HEALTHY_SCORE_THRESHOLD,
            breaker_state=breaker_snapshot.state,
            stats=stats,
        )

    async def get_healthy_channels(
        self,
        channels: Sequence[ExecutionChannel],
    ) -> list[ExecutionChannel]:
        """Filter channels down to those considered healthy.

        The logic is intentionally conservative:
            - if no stats exist, we rely solely on the circuit breaker state,
            - OPEN breakers are considered unhealthy,
            - HALF_OPEN and CLOSED are allowed but scored.
        """
        healthy: list[ExecutionChannel] = []
        for channel in channels:
            score = await self.get_health_score(channel)
            if score is None:
                # With no prior knowledge, we allow the channel but this can be
                # tightened according to governance policies.
                healthy.append(channel)
            elif (
                score.is_healthy and score.breaker_state is not CircuitBreakerState.OPEN
            ):
                healthy.append(channel)

        return healthy

    def _compute_score(
        self,
        stats: ChannelStats,
        breaker_snapshot: CircuitBreakerStateSnapshot,
    ) -> float:
        """Compute a composite health score in [0, 100].

        Current factors:
            - failure rate (penalised non-linearly),
            - average latency (soft penalty),
            - circuit breaker state (hard penalty).
        """
        # Base score
        score = 100.0

        # Failure rate penalty
        failure_rate = stats.failure_rate
        if failure_rate > 0.0:
            score -= min(60.0, failure_rate * 100.0)

        # Latency penalty (if we have a meaningful average)
        avg_latency = stats.average_latency_ms
        if avg_latency is not None:
            # Thresholds can be tuned according to SLOs
            if avg_latency > 500.0:
                score -= 20.0
            elif avg_latency > 200.0:
                score -= 10.0

        # Circuit breaker penalty
        if breaker_snapshot.state is CircuitBreakerState.OPEN:
            score = min(score, DEGRADED_SCORE_THRESHOLD - 10.0)
        elif breaker_snapshot.state is CircuitBreakerState.HALF_OPEN:
            score = min(score, HEALTHY_SCORE_THRESHOLD - 5.0)

        # Clamp to [0, 100]
        return max(0.0, min(100.0, score))
