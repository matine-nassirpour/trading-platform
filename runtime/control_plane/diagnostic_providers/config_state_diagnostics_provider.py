from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from quantum.infrastructure.config.runtime.state.config_state import CONFIG_STATE


@dataclass(frozen=True, slots=True)
class ConfigStateDiagnostics:
    """
    Immutable, deterministic diagnostics for the process-local ConfigState.

    This structure is:
        • View-only (no mutation)
        • Safe to expose in admin dashboards
        • Compatible with Streamlit/JSON export
        • Stable across Python runs
    """

    pid_current: int
    pid_recorded: int
    fork_detected: bool

    base_dir: str | None
    env_file: str | None
    root_param: str | None
    env_file_param: str | None

    cache_size: int
    cache_matches_params: bool
    has_valid_cache: bool

    reload_count: int

    lock_info: Mapping[str, Any]


class ConfigStateDiagnosticsProvider:
    """
    Extracts extended diagnostics from the process-local configuration state.

    Responsibilities:
        • Pure read-only analysis of CONFIG_STATE
        • Never mutates state
        • No I/O
        • Deterministic, safety-grade output
    """

    _reload_counter: int = 0  # Tracks how many times diagnostics were requested
    _last_pid: int | None = None  # PID tracking used to detect forks

    @staticmethod
    def _detect_fork(current_pid: int) -> bool:
        """
        Detects if the process forked since the last diagnostics call.
        """
        last = ConfigStateDiagnosticsProvider._last_pid
        ConfigStateDiagnosticsProvider._last_pid = current_pid

        if last is None:
            return False
        return last != current_pid

    @staticmethod
    def _extract_lock_info() -> Mapping[str, Any]:
        """
        Returns diagnostic-safe information about lock state.
        The actual lock object is not exposed (security + safety).
        """
        lock = CONFIG_STATE._state_lock  # internal but read-only

        locked = lock.locked() if hasattr(lock, "locked") else "unsupported"

        return {
            "locked": locked,
            "owner_thread_id": getattr(lock, "_owner", None),
            "recursion_depth": getattr(lock, "_count", None),
        }

    @staticmethod
    def get() -> ConfigStateDiagnostics:
        """
        Pure extraction of extended ConfigState diagnostics.
        Safe to call frequently.
        """

        state = CONFIG_STATE
        snap = state.snapshot()

        current_pid = snap["pid"]
        fork_detected = ConfigStateDiagnosticsProvider._detect_fork(current_pid)

        # count diagnostic calls (for awareness of observation frequency)
        ConfigStateDiagnosticsProvider._reload_counter += 1

        # evaluate cache health
        cache_matches = state.cache_matches_params(
            root_param=snap["root_param"],
            env_file_param=snap["env_file_param"],
        )

        has_valid_cache = state.has_valid_cache(
            root_param=snap["root_param"],
            env_file_param=snap["env_file_param"],
        )

        lock_info = ConfigStateDiagnosticsProvider._extract_lock_info()

        return ConfigStateDiagnostics(
            pid_current=current_pid,
            pid_recorded=state._pid,
            fork_detected=fork_detected,
            base_dir=snap["base_dir"],
            env_file=snap["env_file"],
            root_param=snap["root_param"],
            env_file_param=snap["env_file_param"],
            cache_size=snap["env_size"],
            cache_matches_params=cache_matches,
            has_valid_cache=has_valid_cache,
            reload_count=ConfigStateDiagnosticsProvider._reload_counter,
            lock_info=lock_info,
        )

    @staticmethod
    def as_dict() -> dict[str, Any]:
        """
        JSON-safe representation for dashboards and HTTP apis.
        """
        diag = ConfigStateDiagnosticsProvider.get()

        return {
            "pid_current": diag.pid_current,
            "pid_recorded": diag.pid_recorded,
            "fork_detected": diag.fork_detected,
            "base_dir": diag.base_dir,
            "env_file": diag.env_file,
            "root_param": diag.root_param,
            "env_file_param": diag.env_file_param,
            "cache_size": diag.cache_size,
            "cache_matches_params": diag.cache_matches_params,
            "has_valid_cache": diag.has_valid_cache,
            "reload_count": diag.reload_count,
            "lock_info": dict(diag.lock_info),
        }
