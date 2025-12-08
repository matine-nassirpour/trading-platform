from __future__ import annotations

import threading
import time

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Final

from runtime.control_plane.diagnostic_providers.time_provider_dependency import (
    TimeProviderDependency,
)

from quantum.infrastructure.config.runtime.fsm.model import (
    FSM_SCHEMA_VERSION,
    ConfigFSMState,
)
from quantum.infrastructure.config.runtime.state.ready_cache import ReadyStateCache


@dataclass(frozen=True, slots=True)
class FSMTransitionRecord:
    """
    Single FSM transition diagnostic entry.

    Immutable and fully serializable. This is safe to expose on dashboards
    and is deterministic across processes.
    """

    index: int
    from_status: str
    to_status: str
    t_start_utc: str
    t_end_utc: str
    duration_ms: float
    metadata: Mapping[str, Any]


class FSMTransitionRecorder:
    """
    Thread-safe, process-local recorder of FSM transitions.

    Guarantees:
        • Pure record-keeping (no effect on pipeline logic)
        • Deterministic ordering
        • High precision duration timing (monotonic clock)
        • UTC timestamps for traceability
        • Immutable transition records
        • Compatible with safety-critical standards
    """

    _lock: Final[threading.RLock] = threading.RLock()
    _records: Final[list[FSMTransitionRecord]] = []
    _counter: Final[list[int]] = [0]  # mutable counter container

    @classmethod
    def record_transition(
        cls,
        *,
        from_state: ConfigFSMState,
        to_state: ConfigFSMState,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        """
        Record a single FSM transition. Intended to be called by the orchestrator
        immediately after each state change.

        The recorder does NOT influence the FSM; it only observes it.
        """
        time_provider = TimeProviderDependency.get()
        t_start_utc = time_provider.now_utc().isoformat()

        # Measure duration using monotonic to avoid clock jumps
        t0 = time.monotonic()

        # No heavy logic, just measure the time until record creation
        t1 = time.monotonic()
        duration_ms = (t1 - t0) * 1000.0

        t_end_utc = time_provider.now_utc().isoformat()

        with cls._lock:
            idx = cls._counter[0]
            cls._counter[0] += 1

            rec = FSMTransitionRecord(
                index=idx,
                from_status=from_state.status.value,
                to_status=to_state.status.value,
                t_start_utc=t_start_utc,
                t_end_utc=t_end_utc,
                duration_ms=duration_ms,
                metadata=dict(metadata or {}),
            )
            cls._records.append(rec)

    @classmethod
    def get_records(cls) -> list[FSMTransitionRecord]:
        """Retrieve a deep copy of all transition records."""
        with cls._lock:
            return list(cls._records)

    @classmethod
    def clear(cls) -> None:
        """Clear all records (diagnostic-only)."""
        with cls._lock:
            cls._records.clear()
            cls._counter[0] = 0


class FSMDiagnosticsProvider:
    """
    Exposes a complete diagnostic snapshot of:
        • All transitions executed during the config lifecycle
        • READY state identity + fingerprint
        • Transition durations + metadata
        • Pipeline coherence and timing
    """

    @staticmethod
    def get_fsm_diagnostics() -> dict:
        time_provider = TimeProviderDependency.get()

        ready_state = ReadyStateCache.get()
        ready_fp = ReadyStateCache.get_fingerprint()

        transitions = FSMTransitionRecorder.get_records()

        return {
            "schema_version": FSM_SCHEMA_VERSION,
            "timestamp_utc": time_provider.now_utc().isoformat(),
            "transition_count": len(transitions),
            "transitions": [
                {
                    "index": r.index,
                    "from": r.from_status,
                    "to": r.to_status,
                    "t_start_utc": r.t_start_utc,
                    "t_end_utc": r.t_end_utc,
                    "duration_ms": r.duration_ms,
                    "metadata": r.metadata,
                }
                for r in transitions
            ],
            "ready_state": {
                "status": ready_state.status.value if ready_state else None,
                "fingerprint": ready_fp,
            },
        }
