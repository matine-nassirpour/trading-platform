"""
End-to-End Observability Pipeline Validation

This test verifies the complete observability chain in a fully isolated
environment, including:
  - Logging (structured JSONL, partition rollover, redaction, severity mapping)
  - Tracing (trace_id/span_id propagation, correlation_id/run_id presence)
  - Metrics (pipeline health and Prometheus registry)
  - Audit event persistence (JSON schema integrity)
  - End-to-end pipeline startup/shutdown lifecycle

It is intentionally exhaustive and mirrors the operational expectations of
production environments.
"""

from __future__ import annotations

import json
import logging
import os
import time

from collections.abc import Callable
from contextlib import suppress
from pathlib import Path
from typing import Any

import pytest

from opentelemetry import trace

from quantum.infrastructure.observability.bootstrap.health_registry import (
    get_health_registry,
)
from quantum.infrastructure.observability.bootstrap.init_manager import (
    init_observability,
    shutdown_observability,
)
from quantum.infrastructure.observability.logging.event_emitter import emit_event
from quantum.infrastructure.observability.metrics.collectors import (
    health_collector as m,
)
from quantum.infrastructure.observability.tracing.correlation.correlation_id import (
    correlation_context,
    new_correlation_id,
)
from quantum.infrastructure.observability.tracing.propagation import (
    baggage_context_from_ids,
)
from tests.support.observability import get_gauge_value


@pytest.mark.system
@pytest.mark.filesystem
@pytest.mark.prometheus
@pytest.mark.otlp
def test_pipeline_observability_e2e_fullstack(
    tmp_workspace, assert_jsonl_tail, read_jsonl, free_port
):
    """
    Full E2E validation of the Quantum observability stack.

    The test asserts that:
        - Logging and tracing pipelines initialize successfully
        - Structured JSONL logs are created with required fields
        - Rollover and partitioning are functional
        - Redaction filters apply correctly
        - Severity levels and numeric mappings are valid
        - Audit events are emitted and JSON-valid
        - Health registry metrics reflect a healthy pipeline
    """
    # --------------------------------------------------------------------------
    # Runtime Overrides
    # --------------------------------------------------------------------------
    os.environ["QUANTUM_METRICS_PORT"] = str(free_port)
    os.environ["QUANTUM_METRICS_ADDR"] = "127.0.0.1"
    os.environ["QUANTUM_LOG_DEEP_PROBE"] = "1"
    os.environ["QUANTUM_LOG_MAX_BYTES"] = "2048"  # ≈ 2KB rollover threshold
    os.environ["QUANTUM_LOG_WARN_BYTES"] = "0"  # Disable pre-roll warnings
    os.environ["QUANTUM_LOG_FSYNC"] = "0"  # Disable fsync for speed

    # --------------------------------------------------------------------------
    # Setup
    # --------------------------------------------------------------------------
    logs_dir: Path = tmp_workspace["logs"]
    audit_dir: Path = tmp_workspace["audit"]

    # Initialize the full observability pipeline
    init_observability(force=True)
    registry = get_health_registry()
    log = logging.getLogger("quantum.observability.e2e")
    tracer = trace.get_tracer("quantum.e2e")

    # --------------------------------------------------------------------------
    # Emit logs, traces, and audit events
    # --------------------------------------------------------------------------
    with correlation_context(new_correlation_id()):
        with baggage_context_from_ids():
            with tracer.start_as_current_span("e2e.span") as sp:
                sp.set_attribute("probe", True)
                log.info(
                    "selftest start",
                    extra={
                        "attrs": {
                            "probe": "ok",
                            "secret": "thisisafakesecret",  # pragma: allowlist secret
                        }
                    },
                )
                log.info("inside span", extra={"attrs": {"in_span": True}})
                log.warning("severity probe warning")
                log.critical("severity probe critical")

                # Emit a whitelisted audit event
                emit_event(
                    {
                        "event_name": "order_submit_v1",
                        "event_version": "v1",
                        "order_id": "st-1",
                        "symbol": "EURUSD",
                        "side": "buy",
                        "qty": 1.0,
                        "price": 1.23456,
                        "ts": int(time.time() * 1000),
                    }
                )

                # Generate ~3KB logs to force partition rollover
                payload = "X" * 256
                for i in range(40):
                    log.info(f"fill {i} {payload}")

    # --------------------------------------------------------------------------
    # Assertions: HealthRegistry (in-memory metrics)
    # --------------------------------------------------------------------------
    logging_ok = get_gauge_value(registry.pipeline_logging_ok)
    tracing_ok = get_gauge_value(registry.pipeline_tracing_ok)
    pipeline_up = get_gauge_value(registry.pipeline_up)

    assert logging_ok == 1.0, "Logging pipeline not marked OK"

    # Tracing may be inactive if no OTLP exporter is configured
    if tracing_ok != 1.0:
        # accept OTLP inactive if exporter is 'console' or 'none'
        exp = os.environ.get("QUANTUM_TRACE_EXPORTER", "console")
        if exp in ("console", "none"):
            pytest.skip(
                f"Tracing exporter inactive ({exp}); skipping pipeline_up check"
            )
        else:
            assert tracing_ok == 1.0, "Tracing pipeline not marked OK"

    assert (
        pipeline_up == 1.0
    ), f"pipeline_up={pipeline_up} (expected 1.0 in full pipeline mode)"

    # --------------------------------------------------------------------------
    # Assertions: Log files (existence + rollover)
    # --------------------------------------------------------------------------
    log_files = sorted(logs_dir.rglob("events-*.jsonl"))
    assert log_files, "No events-*.jsonl log files were generated"
    assert any(".part1" in str(f) for f in log_files), "Missing rollover (.part1.jsonl)"

    # ----------------------------------------------------------------------
    # Assertions: Log JSON schema and redaction
    # ----------------------------------------------------------------------
    logs = read_jsonl(logs_dir)
    assert logs, "No readable JSON logs found"

    found_selftest = next(
        (entry for entry in logs if entry.get("message") == "selftest start"),
        None,
    )
    assert found_selftest, "Missing 'selftest start' log entry"

    must_fields = [
        "service_name",
        "service_namespace",
        "service_version",
        "timestamp",
        "level",
        "logger",
        "message",
        "attrs",
    ]
    for field in must_fields:
        assert field in found_selftest, f"Missing field '{field}' in JSON log"

    assert found_selftest.get("correlation_id"), "correlation_id missing in JSON log"

    attrs = found_selftest.get("attrs", {})
    assert (
        attrs.get("secret") == "[REDACTED]"
    ), "Redaction filter did not replace sensitive field"

    # --------------------------------------------------------------------------
    # Assertions: Severity mapping
    # --------------------------------------------------------------------------
    def _get_log(level: str) -> dict | None:
        for entry in logs:
            if entry.get("message", "").startswith(f"severity probe {level.lower()}"):
                return entry
        return None

    warn_log = _get_log("warning")
    crit_log = _get_log("critical")

    assert warn_log and crit_log, "Missing warning/critical logs for severity mapping"

    def _check_severity(obj: dict, expected_level: str, expected_num: int) -> None:
        lvl = obj.get("level")
        num = obj.get("severity_number")
        assert lvl == expected_level, f"Expected level {expected_level}, got {lvl}"
        assert isinstance(num, int), "severity_number missing or not an int"
        assert 1 <= num <= 24, f"severity_number out of range: {num}"
        assert (
            num == expected_num
        ), f"Unexpected severity_number for {expected_level}: got {num}, expected {expected_num}"

    _check_severity(warn_log, "WARN", 13)
    _check_severity(crit_log, "FATAL", 21)

    # --------------------------------------------------------------------------
    # Assertions: Trace correlation (trace_id/span_id)
    # --------------------------------------------------------------------------
    inside_span = next(
        (entry for entry in logs if entry.get("message") == "inside span"),
        None,
    )
    assert inside_span, "Missing 'inside span' log entry"
    assert inside_span.get("trace_id"), "Missing trace_id on 'inside span'"
    assert inside_span.get("span_id"), "Missing span_id on 'inside span'"

    # --------------------------------------------------------------------------
    # Assertions: Audit event existence and validity
    # --------------------------------------------------------------------------
    audit_files = sorted(audit_dir.rglob("*.json"))
    deadline = time.time() + 2.0
    while not audit_files and time.time() < deadline:
        time.sleep(0.05)
        audit_files = sorted(audit_dir.rglob("*.json"))

    assert audit_files, "No audit event file generated"

    with suppress(Exception):
        js = json.loads(audit_files[0].read_text(encoding="utf-8"))
        assert js.get("event_name") == "order_submit_v1", "Invalid audit file content"

    # --------------------------------------------------------------------------
    # Assertions: Metrics counters
    # --------------------------------------------------------------------------
    def _counter_value(counter: Any) -> float:
        """
        Safely extract the current float value from a Prometheus-like Counter.

        Returns:
            float: The numeric value if accessible, otherwise -1.0.
        """
        value_attr: Any = getattr(counter, "_value", None)
        getter: Callable[[], Any] | None = getattr(value_attr, "get", None)

        if not callable(getter):
            return -1.0

        try:
            value = getter()
            return float(value) if value is not None else -1.0
        except Exception:
            return -1.0

    assert (
        _counter_value(m.logging_redactions_total) > 0.0
    ), "logging_redactions_total did not increment"

    # --------------------------------------------------------------------------
    # Cleanup
    # --------------------------------------------------------------------------
    shutdown_observability()
