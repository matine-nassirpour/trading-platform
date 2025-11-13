from __future__ import annotations

import time

from dataclasses import dataclass

from .health_model import (
    CircuitBreakerConfig,
    CircuitBreakerState,
    CircuitBreakerStateSnapshot,
)


@dataclass(slots=True)
class _CircuitBreakerEntry:
    state: CircuitBreakerState
    consecutive_failures: int
    last_state_change_epoch_s: float
    half_open_trial_count: int = 0


class CircuitBreaker:
    """Async-friendly, per-channel circuit breaker.

    This implementation is deterministic and sideeffect free outside
    its internal state map, making it easy to reason about, test, and audit.

    It does NOT perform any I/O and can be shared across orchestrators
    if desired (with external synchronization).
    """

    def __init__(self, config: CircuitBreakerConfig | None = None) -> None:
        self._config = config or CircuitBreakerConfig()
        self._entries: dict[str, _CircuitBreakerEntry] = {}

    def _get_entry(self, key: str) -> _CircuitBreakerEntry:
        now = time.time()
        entry = self._entries.get(key)
        if entry is None:
            entry = _CircuitBreakerEntry(
                state=CircuitBreakerState.CLOSED,
                consecutive_failures=0,
                last_state_change_epoch_s=now,
                half_open_trial_count=0,
            )
            self._entries[key] = entry
        return entry

    def on_success(self, key: str) -> CircuitBreakerStateSnapshot:
        """Record a successful call for the given key."""
        now = time.time()
        entry = self._get_entry(key)

        # Successful call in HALF_OPEN or OPEN closes the breaker
        if entry.state in (CircuitBreakerState.OPEN, CircuitBreakerState.HALF_OPEN):
            entry.state = CircuitBreakerState.CLOSED
            entry.consecutive_failures = 0
            entry.half_open_trial_count = 0
            entry.last_state_change_epoch_s = now
        else:
            # CLOSED: reset failure counter
            entry.consecutive_failures = 0

        return CircuitBreakerStateSnapshot(
            state=entry.state,
            consecutive_failures=entry.consecutive_failures,
            half_open_trial_count=entry.half_open_trial_count,
            last_state_change_epoch_s=entry.last_state_change_epoch_s,
        )

    def on_failure(self, key: str) -> CircuitBreakerStateSnapshot:
        """Record a failed call for the given key."""
        now = time.time()
        entry = self._get_entry(key)

        entry.consecutive_failures += 1

        if entry.state is CircuitBreakerState.CLOSED:
            if entry.consecutive_failures >= self._config.failure_threshold:
                entry.state = CircuitBreakerState.OPEN
                entry.last_state_change_epoch_s = now

        elif entry.state is CircuitBreakerState.HALF_OPEN:
            # Any failure in HALF_OPEN sends us back to OPEN
            entry.state = CircuitBreakerState.OPEN
            entry.last_state_change_epoch_s = now
            entry.half_open_trial_count = 0

        return CircuitBreakerStateSnapshot(
            state=entry.state,
            consecutive_failures=entry.consecutive_failures,
            half_open_trial_count=entry.half_open_trial_count,
            last_state_change_epoch_s=entry.last_state_change_epoch_s,
        )

    def can_attempt(self, key: str) -> CircuitBreakerStateSnapshot:
        """Check whether a call is allowed for the given key.

        This should be invoked before dispatching a call. The caller can then
        decide to:
            - route elsewhere,
            - reject the request,
            - or proceed knowing the state.
        """
        now = time.time()
        entry = self._get_entry(key)

        if entry.state is CircuitBreakerState.OPEN:
            elapsed = now - entry.last_state_change_epoch_s
            if elapsed >= self._config.open_duration_s:
                # Transition to HALF_OPEN and allow a limited number of trials
                entry.state = CircuitBreakerState.HALF_OPEN
                entry.half_open_trial_count = 0
                entry.last_state_change_epoch_s = now

        if entry.state is CircuitBreakerState.HALF_OPEN:
            entry.half_open_trial_count += 1
            if entry.half_open_trial_count > self._config.half_open_max_calls:
                # Too many half-open trials without a reset -> OPEN again
                entry.state = CircuitBreakerState.OPEN
                entry.last_state_change_epoch_s = now

        return CircuitBreakerStateSnapshot(
            state=entry.state,
            consecutive_failures=entry.consecutive_failures,
            half_open_trial_count=entry.half_open_trial_count,
            last_state_change_epoch_s=entry.last_state_change_epoch_s,
        )
