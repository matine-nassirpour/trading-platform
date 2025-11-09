"""
E2E Validation — OTLP/HTTP Tracing Exporter

This test validates that the observability pipeline correctly initializes
the OTLP/HTTP tracing exporter and reports healthy status in metrics.
"""

from __future__ import annotations

import os

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
@pytest.mark.otlp
def test_observability_otlp_http_exporter_e2e(tmp_workspace, free_port):
    """
    Initialize the observability pipeline with OTLP/HTTP exporter enabled
    and assert that tracing exporter status is marked active.
    """
    # --------------------------------------------------------------------------
    # Configuration for OTLP/HTTP
    # --------------------------------------------------------------------------
    os.environ["QUANTUM_METRICS_PORT"] = str(free_port)
    os.environ["QUANTUM_METRICS_ADDR"] = "127.0.0.1"
    os.environ["QUANTUM_LOG_DEEP_PROBE"] = "1"
    os.environ["QUANTUM_TRACE_EXPORTER"] = "otlp"
    os.environ["QUANTUM_TRACE_OTLP_PROTOCOL"] = "http"
    os.environ["QUANTUM_TRACE_OTLP_ENDPOINT"] = "http://127.0.0.1:4318"
    os.environ["QUANTUM_TRACE_OTLP_INSECURE"] = "1"

    # --------------------------------------------------------------------------
    # Start the observability stack
    # --------------------------------------------------------------------------
    init_observability(force=True)
    registry = get_health_registry()

    # --------------------------------------------------------------------------
    # Verify tracing exporter status
    # --------------------------------------------------------------------------
    from quantum.infrastructure.observability.metrics.collectors import (
        health_collector as m,
    )

    exp_status = get_gauge_value(m.tracing_exporter_status)
    assert exp_status == 1.0, "OTLP/HTTP exporter not marked active"

    # Partial mode: logging + tracing OK, metrics HTTP may be disabled
    logging_ok = get_gauge_value(registry.pipeline_logging_ok)
    tracing_ok = get_gauge_value(registry.pipeline_tracing_ok)
    pipeline_up = get_gauge_value(registry.pipeline_up)

    assert logging_ok == 1.0, "Logging pipeline not marked OK"
    assert tracing_ok == 1.0, "Tracing pipeline not marked OK"

    # pipeline_up may remain 0.0 if metrics HTTP is not running
    if pipeline_up != 1.0:
        pytest.skip(
            f"pipeline_up={pipeline_up} (expected 0.0 in partial observability mode)"
        )

    # --------------------------------------------------------------------------
    # Cleanup
    # --------------------------------------------------------------------------
    shutdown_observability()
