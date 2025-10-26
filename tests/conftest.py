"""
Goals: full test hermeticity, no shared state, and zero FD/handler leaks.
- Isolated environment variables per test
- Isolated Prometheus registry per test
- Sealed temporary workspace for filesystem interactions
- Defensive teardown for logging handlers between tests
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import sys
import tempfile
import threading
import time
from collections.abc import Callable, Generator
from contextlib import contextmanager, suppress
from pathlib import Path

import pytest

from quantum.core.config.models.core import CoreSettings
from quantum.core.config.models.logging import LoggingSettings
from tests.support.types import Workspace

_LOG_CLEANUP_LOCK = threading.Lock()

# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ sys.path: add "src/" to the test runner's PYTHONPATH                        │
# ╰─────────────────────────────────────────────────────────────────────────────╯
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_SRC = _PROJECT_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))  # prefer local sources during tests


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ General tools                                                               │
# ╰─────────────────────────────────────────────────────────────────────────────╯
@contextmanager
def _preserve_environ():
    """Save/restore a snapshot of os.environ (key/value)."""
    snapshot = dict(os.environ)
    try:
        yield
    finally:
        # Purge everything added/modified during testing
        to_del = set(os.environ.keys()) - set(snapshot.keys())
        for k in to_del:
            with suppress(KeyError):
                del os.environ[k]
        for k, v in snapshot.items():
            os.environ[k] = v


def _read_tail_complete_lines(
    path: Path, *, chunk_bytes: int, encoding: str = "utf-8"
) -> list[str]:
    """
    Read the tail of a JSONL file, preserving only complete lines.

    Robust to rotations/permissions/encoding:
    - Seeks near the end of file (chunk_bytes)
    - Drops a potentially truncated first/last line
    - Normalizes newlines
    """
    try:
        with open(path, "rb") as fh:
            fh.seek(0, os.SEEK_END)
            file_end = fh.tell()
            start_offset = max(0, file_end - chunk_bytes)
            fh.seek(start_offset)
            buf = fh.read().decode(encoding, "replace")

        if start_offset > 0:
            buf = buf.split("\n", 1)[-1]  # drop possibly truncated first line

        buf = buf.replace("\r\n", "\n")
        raw_lines = buf.split("\n")

        if raw_lines and buf and not buf.endswith("\n"):
            raw_lines = raw_lines[:-1]  # drop last incomplete line

        return [line for line in raw_lines if line.strip()]
    except (OSError, UnicodeDecodeError):
        return []


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Fixtures                                                                    │
# ╰─────────────────────────────────────────────────────────────────────────────╯
@pytest.fixture
def fake_env_file(tmp_path: Path) -> Path:
    """
    Create a temporary fake .env file for deterministic environment loading tests.
    """
    env_content = "\n".join(
        [
            "QUANTUM_APP_NAME=test_app",
            "QUANTUM_ENV=dev",
            "QUANTUM_LOG_LEVEL=INFO",
            "QUANTUM_TRACE_EXPORTER=console",
            "QUANTUM_METRICS_PORT=0",
        ]
    )
    env_file = tmp_path / ".env"
    env_file.write_text(env_content, encoding="utf-8")
    return env_file


@pytest.fixture(scope="function")
def iso_env():
    """
    Isolate the process environment for a single test function.

    Fully restores os.environ during teardown. Ensures any change to environment
    variables in one test does not leak to the next one.
    """
    with _preserve_environ():
        yield


@pytest.fixture(scope="function")
def clean_registry(monkeypatch):
    """
    Isolate the Prometheus registry per test (Counter/Gauge/Histogram).

    Avoids metric name collisions and shared state across tests by providing
    a fresh CollectorRegistry and monkeypatching common access points.
    """
    try:
        import prometheus_client
        from prometheus_client import CollectorRegistry
        from prometheus_client import core as pc_core
    except Exception:
        # Prometheus not present / not used by the test
        yield
        return

    reg = CollectorRegistry()

    # Monkeypatch the most common access points
    monkeypatch.setattr(prometheus_client, "REGISTRY", reg, raising=False)
    monkeypatch.setattr(pc_core, "REGISTRY", reg, raising=False)

    yield


@pytest.fixture(scope="function")
def tmp_workspace(iso_env, clean_registry) -> Generator[Workspace]:
    """
    Create a temporary, sealed workspace with subfolders: `_logs` and `_audit`.

    Exports QUANTUM_* environment variables to point to those folders and
    configures defaults for a quiet but functional observability pipeline.

    Returns:
        dict[str, Path]: mapping with keys "root", "logs", "audit".
    """
    tmpdir = Path(tempfile.mkdtemp(prefix="quantum_test_"))
    log_dir = tmpdir / "_logs"
    audit_dir = tmpdir / "_audit"
    log_dir.mkdir(parents=True, exist_ok=True)
    audit_dir.mkdir(parents=True, exist_ok=True)

    # Default ENV for a quiet but functional pipeline
    os.environ.setdefault("QUANTUM_APP_NAME", "test_app")
    os.environ.setdefault("QUANTUM_APP_VERSION", "0.0.0+test")
    os.environ.setdefault("QUANTUM_ENV", "test")
    os.environ.setdefault("QUANTUM_NS", "quantum")

    os.environ["QUANTUM_LOG_DIR"] = str(log_dir)
    os.environ["QUANTUM_AUDIT_DIR"] = str(audit_dir)

    # No Prometheus HTTP exposure in unit tests
    os.environ.setdefault("QUANTUM_METRICS_PORT", "0")

    # Shortcuts & safety (faster, deterministic)
    os.environ.setdefault("QUANTUM_LOG_FSYNC", "0")
    os.environ.setdefault("QUANTUM_LOG_RATELIMIT", "0")
    os.environ.setdefault("QUANTUM_LOG_SAMPLE_INFO", "")
    os.environ.setdefault("QUANTUM_LOG_MAX_BYTES", "1048576")  # 1 MiB
    os.environ.setdefault("QUANTUM_LOG_WARN_BYTES", "0")
    os.environ.setdefault("QUANTUM_TRACE_SAMPLE", "1.0")
    os.environ.setdefault("QUANTUM_TRACE_EXPORTER", "console")
    os.environ.setdefault("QUANTUM_AUDIT_EVENTS_VERSION", "v1")
    os.environ.setdefault("QUANTUM_AUDIT_EVENTS", "order_submit_v1")

    payload: Workspace = {"root": tmpdir, "logs": log_dir, "audit": audit_dir}

    try:
        yield payload
    finally:
        # Teardown: pipeline shutdown + cleanup
        with suppress(Exception):
            from quantum.infrastructure.observability.bootstrap.init_manager import (
                shutdown_observability,
            )

            shutdown_observability(
                close_logging=True,
                shutdown_tracing=True,
                reset_state=True,
                set_gauges_down=True,
            )

        # Defensive closure of any residual handler
        _close_all_handlers()

        # Cleaning the workspace
        with suppress(Exception):
            shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def cap_config_logs(caplog):
    """
    Capture all logs emitted by the Quantum configuration subsystem.
    """
    caplog.set_level(logging.DEBUG, logger="quantum.config")
    yield caplog


@pytest.fixture
def valid_core_settings(tmp_workspace) -> CoreSettings:
    """Return a valid CoreSettings instance using the temporary workspace."""
    from quantum.core.config.runtime.manager import ConfigManager

    return ConfigManager.load(apply=False)


@pytest.fixture
def base_settings(tmp_path: Path) -> CoreSettings:
    """Return minimal Settings pointing logs under tmp_path."""
    return CoreSettings(
        quantum_app_name="test_app",
        quantum_app_version="0.0.0+test",
        quantum_env="test",
        quantum_ns="quantum",
        quantum_metrics_port=0,
    )


@pytest.fixture(scope="function")
def make_observability(tmp_workspace):
    """Factory fixture to build ObservabilitySettings with test-safe defaults."""

    def _factory(**overrides) -> LoggingSettings:
        defaults = dict(
            quantum_log_dir=str(tmp_workspace["logs"]),
            quantum_audit_dir=str(tmp_workspace["audit"]),
            quantum_log_fsync=False,
            quantum_log_max_bytes=0,
            quantum_log_warn_bytes=0,
        )
        return LoggingSettings(**{**defaults, **overrides})

    return _factory


@pytest.fixture(scope="function")
def no_rate_limit_no_sampling():
    """
    Disable INFO sampling and rate limiting for tests that assert presence of logs.

    This reduces flakiness for tests that need to observe records deterministically.
    """
    prev = {
        "QUANTUM_LOG_RATELIMIT": os.environ.get("QUANTUM_LOG_RATELIMIT"),
        "QUANTUM_LOG_RPS": os.environ.get("QUANTUM_LOG_RPS"),
        "QUANTUM_LOG_SAMPLE_INFO": os.environ.get("QUANTUM_LOG_SAMPLE_INFO"),
    }
    os.environ["QUANTUM_LOG_RATELIMIT"] = "0"
    os.environ["QUANTUM_LOG_RPS"] = "1000000"
    os.environ["QUANTUM_LOG_SAMPLE_INFO"] = ""
    try:
        yield
    finally:
        for k, v in prev.items():
            if v is None:
                with suppress(KeyError):
                    del os.environ[k]
            else:
                os.environ[k] = v


@pytest.fixture(scope="function")
def obs_session(tmp_workspace):
    """
    Open a full observability session in a controlled context and guarantee
    a clean closure (freeing FDs/handlers).
    """
    from quantum.infrastructure.observability.bootstrap.init_manager import (
        observability_session,
    )

    with observability_session(
        force=True,
    ):
        yield

    # Safety (observability_session already performs the shutdown)
    _close_all_handlers()


@pytest.fixture(scope="function")
def monotonic_stepper(monkeypatch):
    """
    Monkeypatch time.monotonic_ns() with a deterministic generator.
    Useful for stabilizing latency/rollover measurements across tests.
    """
    step_ns = 5_000_000  # 5 ms
    t = 1_000_000_000_000  # arbitrary base in ns

    def _fake_monotonic_ns():
        nonlocal t
        t += step_ns
        return t

    monkeypatch.setattr(time, "monotonic_ns", _fake_monotonic_ns)
    yield


@pytest.fixture
def free_port() -> int:
    """
    Return an available TCP port bound on 127.0.0.1 for ephemeral use in tests.

    Thread-safe and reliable across OSes. Used by tests that need a temporary
    HTTP or gRPC listener (e.g. Prometheus /metrics, OTLP exporters, etc.).
    """
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ JSONL Reading Helpers for Assertions                                        │
# ╰─────────────────────────────────────────────────────────────────────────────╯
@pytest.fixture(scope="function")
def read_jsonl():
    """
    Return a function: (base_dir, pattern, chunk_bytes=...) -> list[dict]
    Reads the latest JSON objects from JSONL files (tail), skipping invalid lines.
    """

    def _reader(
        base_dir: Path, pattern: str = "events-*.jsonl", *, chunk_bytes: int = 256_000
    ) -> list[dict]:
        files = sorted(
            Path(base_dir).rglob(pattern),
            key=lambda p: p.stat().st_mtime if p.exists() else 0.0,
            reverse=False,  # oldest → newest
        )
        out: list[dict] = []
        for fp in files:
            for line in _read_tail_complete_lines(fp, chunk_bytes=chunk_bytes):
                with suppress(json.JSONDecodeError, TypeError):
                    out.append(json.loads(line))
        return out

    return _reader


@pytest.fixture(scope="function")
def assert_jsonl_tail(read_jsonl):
    """
    Return a convenient assertion function on the JSONL tail.

    Usage:
        assert_jsonl_tail(
            base_dir,
            match=lambda obj: bool,
            min_count=1,
            pattern="events-*.jsonl",
            timeout_s=1.5,
            poll_s=0.05,
        ) -> list[dict]
    """

    def _assert(
        base_dir: Path,
        *,
        match: Callable[[dict], bool],
        min_count: int = 1,
        pattern: str = "events-*.jsonl",
        timeout_s: float = 1.5,
        poll_s: float = 0.05,
    ) -> list[dict]:
        deadline = time.time() + timeout_s
        last: list[dict] = []
        while time.time() < deadline:
            objs = read_jsonl(base_dir, pattern=pattern)
            last = objs
            hits = [o for o in objs if _safe_bool(match, o)]
            if len(hits) >= min_count:
                return hits
            time.sleep(poll_s)
        # Failure → explicit raise with hint
        raise AssertionError(
            f"Expected at least {min_count} matching JSON logs in tail, "
            f"got {len([o for o in last if _safe_bool(match, o)])}.\n"
            f"Scanned files under: {base_dir} (pattern={pattern})"
        )

    return _assert


def _safe_bool(fn: Callable[[dict], bool], obj: dict) -> bool:
    with suppress(Exception):
        return bool(fn(obj))
    return False


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Defensive global teardown: closing handlers between tests                   │
# ╰─────────────────────────────────────────────────────────────────────────────╯
def _iter_all_loggers() -> list[logging.Logger]:
    """
    Return all known loggers including root and children registered in the manager.

    This helps aggressively close/flush every handler that may have been added
    by the code under test, avoiding FD leaks across tests.
    """
    # Start with root
    loggers: list[logging.Logger] = [logging.getLogger()]
    # Add any named loggers present in the registry
    for name in list(logging.root.manager.loggerDict.keys()):
        try:
            loggers.append(logging.getLogger(name))
        except Exception:
            # Defensive: ignore malformed entries
            continue
    return loggers


def _close_all_handlers():
    """
    Cleanly flush/close and detach all handlers of all known loggers.

    Thread-safe: ensures that only one cleanup operation runs at a time,
    preventing race conditions under pytest-xdist or multithreaded tests.
    """
    with _LOG_CLEANUP_LOCK:
        for logger in _iter_all_loggers():
            for h in list(logger.handlers):
                with suppress(Exception):
                    h.flush()
                with suppress(Exception):
                    h.close()
                with suppress(Exception):
                    logger.removeHandler(h)


@pytest.fixture(autouse=True)
def _auto_cleanup_handlers():
    """
    Auto-use fixture: if a test forgets to close the pipeline,
    we clean up the handlers after each test to avoid FD leaks.

    Cost note: this scans the logger registry per test; keep it lightweight in your
    code under test to avoid registering an excessive number of loggers.
    """
    yield
    _close_all_handlers()


@pytest.fixture(autouse=True)
def reset_config_state():
    """
    Automatically reset ConfigManager caches and ConfigState between tests.

    Ensures no residual environment or LRU cache contamination between tests,
    preserving hermeticity for configuration-dependent modules.
    """
    from quantum.core.config.runtime.manager import ConfigManager
    from quantum.core.config.runtime.state import ConfigState

    ConfigManager.clear_caches()
    ConfigState.instance().reset()
    yield
    ConfigManager.clear_caches()
    ConfigState.instance().reset()


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Pytest configuration hooks                                                  │
# ╰─────────────────────────────────────────────────────────────────────────────╯
def pytest_configure(config: pytest.Config) -> None:
    """
    Register commonly used custom markers to avoid warnings and improve test filtering.
    """
    for marker in ("unit", "filesystem", "prometheus", "otlp", "e2e"):
        config.addinivalue_line("markers", marker)
