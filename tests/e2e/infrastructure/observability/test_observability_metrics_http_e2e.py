"""
E2E Validation — /metrics HTTP endpoint availability

This test extends the core observability pipeline test by enabling
the embedded Prometheus HTTP endpoint and verifying that it exposes
the `quantum_pipeline_up 1` metric successfully.
"""

from __future__ import annotations

import os
import time
import urllib.request

import pytest

from quantum.infrastructure.observability.bootstrap.health_registry import (
    get_health_registry,
)
from quantum.infrastructure.observability.bootstrap.init_manager import (
    init_observability,
    shutdown_observability,
)
from tests.support.observability import get_gauge_value


@pytest.mark.e2e
@pytest.mark.prometheus
@pytest.mark.filesystem
def test_observability_metrics_http_probe_e2e(tmp_workspace):
    """
    Launch the observability pipeline with HTTP metrics enabled and
    ensure that /metrics endpoint is reachable and reports healthy metrics.
    """
    # --------------------------------------------------------------------------
    # Configuration: enable /metrics endpoint
    # --------------------------------------------------------------------------
    port = 9099  # arbitrary free port for local test
    os.environ["QUANTUM_METRICS_PORT"] = str(port)
    os.environ["QUANTUM_METRICS_ADDR"] = "127.0.0.1"
    os.environ["QUANTUM_LOG_DEEP_PROBE"] = "1"

    # --------------------------------------------------------------------------
    # Start the observability stack
    # --------------------------------------------------------------------------
    init_observability(force=True)
    registry = get_health_registry()

    # Wait for server startup
    time.sleep(0.2)

    # --------------------------------------------------------------------------
    # Verify that the /metrics endpoint is live
    # --------------------------------------------------------------------------
    url = f"http://127.0.0.1:{port}/metrics"
    try:
        with urllib.request.urlopen(url, timeout=2.0) as resp:
            body = resp.read().decode("utf-8", "replace")
        assert "quantum_pipeline_up 1" in body, "/metrics missing quantum_pipeline_up 1"
    except Exception as e:
        pytest.fail(f"/metrics endpoint unavailable or invalid: {e}")

    # --------------------------------------------------------------------------
    # Registry validation (basic)
    # --------------------------------------------------------------------------
    assert get_gauge_value(registry.pipeline_metrics_http_ok) == 1.0
    assert get_gauge_value(registry.pipeline_up) == 1.0

    # --------------------------------------------------------------------------
    # Cleanup
    # --------------------------------------------------------------------------
    shutdown_observability()
