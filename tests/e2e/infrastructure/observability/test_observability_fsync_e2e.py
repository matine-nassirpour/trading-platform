"""
E2E Validation — Logging Durability (fsync mode)

This test validates the observability logging subsystem when durability
is enforced via fsync() after each log write. It ensures that log files
are created, flushed to disk, and contain valid JSONL entries.
"""

from __future__ import annotations

import json
import logging
import os
import time

from pathlib import Path

import pytest

from quantum.infrastructure.observability.bootstrap.health_registry import (
    get_health_registry,
)
from quantum.infrastructure.observability.bootstrap.init_manager import (
    init_observability,
    shutdown_observability,
)
from tests.support.observability import get_gauge_value


@pytest.mark.system
@pytest.mark.filesystem
def test_observability_logging_fsync_e2e(tmp_workspace):
    """
    Enable QUANTUM_LOG_FSYNC=1 and verify that logs are safely flushed
    and partition files are immediately visible and readable after writes.
    """
    # --------------------------------------------------------------------------
    # Configuration: enforce fsync mode
    # --------------------------------------------------------------------------
    os.environ["QUANTUM_LOG_FSYNC"] = "1"
    os.environ["QUANTUM_LOG_MAX_BYTES"] = "2048"  # small to trigger rollover
    os.environ["QUANTUM_LOG_WARN_BYTES"] = "0"

    # --------------------------------------------------------------------------
    # Initialize the observability stack
    # --------------------------------------------------------------------------
    init_observability(force=True)

    # Note:
    # The "[WARNING] OTLP exporter inactive" log message may appear here.
    # This is expected in test mode when no external OpenTelemetry collector
    # endpoint is configured. It does *not* indicate a failure of the pipeline
    # or a misconfiguration — only that the tracing exporter is disabled.

    registry = get_health_registry()
    log = logging.getLogger("fsync.test")

    # --------------------------------------------------------------------------
    # Emit a small burst of logs
    # --------------------------------------------------------------------------
    payload = "Y" * 256
    for i in range(20):
        log.info(f"fsync test line {i} {payload}")

    # Allow minimal delay for I/O flushes
    time.sleep(0.2)

    # --------------------------------------------------------------------------
    # Assertions: verify log files exist and are flushed
    # --------------------------------------------------------------------------
    logs_dir: Path = tmp_workspace["logs"]
    log_files = sorted(logs_dir.rglob("events-*.jsonl"))
    assert log_files, "No log files found under fsync mode"

    # At least one file should have non-zero size and be readable
    readable_found = False
    for fp in log_files:
        if fp.stat().st_size == 0:
            continue
        try:
            with open(fp, encoding="utf-8") as f:
                for line in f:
                    json.loads(line)
                    readable_found = True
                    break
        except Exception:
            continue

    assert readable_found, "No valid JSONL entries readable from fsync logs"

    # --------------------------------------------------------------------------
    # Health metrics validation
    # --------------------------------------------------------------------------
    logging_ok = get_gauge_value(registry.pipeline_logging_ok)
    assert logging_ok == 1.0, "Logging pipeline not marked OK under fsync mode"

    # --------------------------------------------------------------------------
    # Cleanup
    # --------------------------------------------------------------------------
    shutdown_observability()
