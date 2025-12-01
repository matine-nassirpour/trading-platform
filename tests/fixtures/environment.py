import os
import shutil
import tempfile

from collections.abc import Generator
from contextlib import contextmanager, suppress
from pathlib import Path

import pytest

from tests.support.logging_utils import close_all_handlers
from tests.support.types import Workspace


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


@pytest.fixture(scope="function")
def iso_env():
    """
    Isolate the process environment for a single test function.

    Fully restores os.environ during teardown. Ensures any change to environment
    variables in one test does not leak to the next one.
    """
    with _preserve_environ():
        yield


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
    os.environ.setdefault("QUANTUM_AUDIT_ALLOWLIST", "order_submit_v1")

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
        close_all_handlers()

        # Cleaning the workspace
        with suppress(Exception):
            shutil.rmtree(tmpdir, ignore_errors=True)


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
