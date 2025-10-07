"""
Goals: Hermeticity, no shared states, zero FD/handler leaks.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import sys
import tempfile
import time
from collections.abc import Callable
from contextlib import contextmanager, suppress
from pathlib import Path

import pytest

# ──────────────────────────────────────────────────────────────────────────────
# sys.path: add "src/" to the test runner's PYTHONPATH
# ──────────────────────────────────────────────────────────────────────────────
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_SRC = _PROJECT_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))  # priority to the local version


# ──────────────────────────────────────────────────────────────────────────────
# General tools
# ──────────────────────────────────────────────────────────────────────────────
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
    Reads the end of a JSONL file, preserving only complete lines.
    Robust to rotations/permissions/encoding.
    """
    try:
        with open(path, "rb") as fh:
            fh.seek(0, os.SEEK_END)
            file_end = fh.tell()
            start_offset = max(0, file_end - chunk_bytes)
            fh.seek(start_offset)
            buf = fh.read().decode(encoding, "replace")

        if start_offset > 0:
            buf = buf.split("\n", 1)[-1]  # drop 1st line potentially truncated

        buf = buf.replace("\r\n", "\n")
        raw_lines = buf.split("\n")

        if raw_lines and buf and not buf.endswith("\n"):
            raw_lines = raw_lines[:-1]  # drop last incomplete line

        return [line for line in raw_lines if line.strip()]
    except (OSError, UnicodeDecodeError):
        return []


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────
@pytest.fixture(scope="function")
def iso_env():
    """
    Isolates the process environment for testing.
    Fully restores os.environ in teardown.
    """
    with _preserve_environ():
        yield


@pytest.fixture(scope="function")
def clean_registry(monkeypatch):
    """
    Isolates the Prometheus registry per test (Counter/Gauge/Histogram).
    Avoids name collisions and shared state between tests.
    """
    try:
        import prometheus_client
        from prometheus_client import CollectorRegistry
        from prometheus_client import core as pc_core
    except Exception:
        # Prometheus not present / not used in the test
        yield
        return

    reg = CollectorRegistry()

    # Monkeypatch the most common access points
    monkeypatch.setattr(prometheus_client, "REGISTRY", reg, raising=False)
    monkeypatch.setattr(pc_core, "REGISTRY", reg, raising=False)

    yield


@pytest.fixture(scope="function")
def tmp_workspace(iso_env, clean_registry):
    """
    Create a temporary, sealed workspace with _logs and _audit.
    Export the necessary QUANTUM_* variables and clean up in teardown.
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

    # Shortcuts & Safety
    os.environ.setdefault("QUANTUM_LOG_FSYNC", "0")  # faster
    os.environ.setdefault("QUANTUM_LOG_RATELIMIT", "0")  # no drop
    os.environ.setdefault("QUANTUM_LOG_SAMPLE_INFO", "")  # no sampling
    os.environ.setdefault("QUANTUM_LOG_MAX_BYTES", "1048576")  # 1 MiB
    os.environ.setdefault("QUANTUM_LOG_WARN_BYTES", "0")
    os.environ.setdefault("QUANTUM_TRACE_SAMPLE", "1.0")
    os.environ.setdefault("QUANTUM_TRACE_EXPORTER", "console")
    os.environ.setdefault("QUANTUM_AUDIT_EVENTS_VERSION", "v1")
    os.environ.setdefault("QUANTUM_AUDIT_EVENTS", "order_submit_v1")

    try:
        yield {"root": tmpdir, "logs": log_dir, "audit": audit_dir}
    finally:
        # Teardown: pipeline shutdown + cleanup
        with suppress(Exception):
            from quantum.infrastructure.observability.init_observability import (
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


@pytest.fixture(scope="function")
def no_rate_limit_no_sampling():
    """
    Disables rate limiting and sampling INFO for tests that validate
    the presence of inputs (less flakiness).
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
    Opens a full observability session in a controlled context,
    and guarantees a clean closure (freeing FDs/handlers).
    """
    from quantum.infrastructure.observability.init_observability import (
        observability_session,
    )

    with observability_session(
        app_name=os.environ.get("QUANTUM_APP_NAME", "test_app"),
        environment=os.environ.get("QUANTUM_ENV", "test"),
        namespace=os.environ.get("QUANTUM_NS", "quantum"),
        log_level=os.environ.get("QUANTUM_LOG_LEVEL", "INFO"),
        sample_ratio=float(os.environ.get("QUANTUM_TRACE_SAMPLE", "1.0")),
        force=True,
    ):
        yield

    # For security (observability_session already does the shutdown)
    _close_all_handlers()


@pytest.fixture(scope="function")
def monotonic_stepper(monkeypatch):
    """
    Monkeypatches time.monotonic_ns() with a deterministic generator.
    Useful for stabilizing latency/rollover measurements.
    """
    step_ns = 5_000_000  # 5 ms
    t = 1_000_000_000_000  # arbitrary base in ns

    def _fake_monotonic_ns():
        nonlocal t
        t += step_ns
        return t

    monkeypatch.setattr(time, "monotonic_ns", _fake_monotonic_ns)
    yield


# ──────────────────────────────────────────────────────────────────────────────
# JSONL Reading Helpers for Assertions
# ──────────────────────────────────────────────────────────────────────────────
@pytest.fixture(scope="function")
def read_jsonl():
    """
    Returns a function: (base_dir, pattern, chunk_bytes=...) -> list[dict]
    Robust reading inspired by the Streamlit page (only valid JSON).
    """

    def _reader(
        base_dir: Path, pattern: str = "events-*.jsonl", *, chunk_bytes: int = 256_000
    ) -> list[dict]:
        files = sorted(
            Path(base_dir).rglob(pattern),
            key=lambda p: p.stat().st_mtime if p.exists() else 0.0,
            reverse=True,
        )
        out: list[dict] = []
        for fp in files[:2]:
            for line in _read_tail_complete_lines(fp, chunk_bytes=chunk_bytes):
                with suppress(json.JSONDecodeError, TypeError):
                    out.append(json.loads(line))
        return out

    return _reader


@pytest.fixture(scope="function")
def assert_jsonl_tail(read_jsonl):
    """
    Returns a convenient assertion function on the JSONL tail:
    assert_jsonl_tail(base_dir, match=lambda obj: bool, min_count=1, pattern='events-*.jsonl')
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
            f"Expected at least {min_count} matching JSON logs in tail, got {len([o for o in last if _safe_bool(match, o)])}.\n"
            f"Scanned files under: {base_dir} (pattern={pattern})"
        )

    return _assert


def _safe_bool(fn: Callable[[dict], bool], obj: dict) -> bool:
    with suppress(Exception):
        return bool(fn(obj))
    return False


# ──────────────────────────────────────────────────────────────────────────────
# Defensive global teardown: closing handlers between tests
# ──────────────────────────────────────────────────────────────────────────────
def _close_all_handlers():
    """Cleanly closes and detaches all known logger handlers."""
    for name in ("", "quantum.trading"):
        logger = logging.getLogger(name)
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
    Auto-use fixture: In case a test forgets to close the pipeline,
    we clean up the handlers after each test to avoid FD leaks.
    """
    yield
    _close_all_handlers()


# ──────────────────────────────────────────────────────────────────────────────
# Quality of life: more readable pytest logging (optional)
# ──────────────────────────────────────────────────────────────────────────────
def pytest_configure(config):
    # By default, we let pytest handle the capture. Nothing mandatory here.
    pass
