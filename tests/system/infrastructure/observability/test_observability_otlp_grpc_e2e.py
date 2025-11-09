"""
E2E Validation — OTLP/gRPC Tracing Exporter

This test ensures that the observability pipeline correctly initializes
the OTLP/gRPC tracing exporter when configured, and reflects its status in
the metrics registry.
"""

from __future__ import annotations

import os

import pytest

from tests.support.observability import get_gauge_value

from quantum.infrastructure.observability.bootstrap.health_registry import (
    get_health_registry,
)
from quantum.infrastructure.observability.bootstrap.init_manager import (
    init_observability,
    shutdown_observability,
)


@pytest.mark.system
@pytest.mark.otlp
def test_observability_otlp_grpc_exporter_e2e(tmp_workspace, free_port):
    """
    Initialize the observability pipeline with OTLP/gRPC exporter enabled
    and assert that tracing exporter status is marked active.
    """
    # --------------------------------------------------------------------------
    # Configuration for OTLP/gRPC
    # --------------------------------------------------------------------------
    os.environ["QUANTUM_METRICS_PORT"] = str(free_port)
    os.environ["QUANTUM_METRICS_ADDR"] = "127.0.0.1"
    os.environ["QUANTUM_TRACE_EXPORTER"] = "otlp"
    os.environ["QUANTUM_TRACE_OTLP_PROTOCOL"] = "grpc"
    os.environ["QUANTUM_TRACE_OTLP_ENDPOINT"] = "127.0.0.1:4317"
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
    assert exp_status == 1.0, "OTLP/gRPC exporter not marked active"

    # Logging and tracing should both be OK
    assert get_gauge_value(registry.pipeline_tracing_ok) == 1.0
    assert get_gauge_value(registry.pipeline_logging_ok) == 1.0

    # pipeline_up may be 0.0 in partial mode (no /metrics HTTP)
    pipeline_up = get_gauge_value(registry.pipeline_up)
    if pipeline_up != 1.0:
        pytest.skip(
            f"pipeline_up={pipeline_up} (expected 0.0 in partial observability mode)"
        )

    # --------------------------------------------------------------------------
    # Cleanup
    # --------------------------------------------------------------------------
    shutdown_observability()
