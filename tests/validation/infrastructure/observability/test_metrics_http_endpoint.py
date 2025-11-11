from __future__ import annotations

import logging
import os
import socket
import urllib.request

from typing import Final

import pytest

from tests.support.wait import wait_until


def _free_port() -> int:
    """Return a free TCP port on 127.0.0.1 (bind-reserve-then-release)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.mark.validation
@pytest.mark.usefixtures("no_rate_limit_no_sampling")
class TestMetricsHTTPEndpoint:
    def test_metrics_http_endpoint_exposes_core_metrics(self, tmp_workspace, tmp_path):
        """
        Start /metrics (Prometheus) and verify:

          - presence of 'quantum_pipeline_up 1'
          - redaction counter exposed after a secret is logged
          - file rotation counter exposed after a burst with a small QUANTUM_LOG_MAX_BYTES
        """
        from quantum.infrastructure.observability.bootstrap.init_manager import (
            init_observability,
            shutdown_observability,
        )

        # Choose a free port
        port = _free_port()
        addr: Final = "127.0.0.1"

        # ENV
        os.environ["QUANTUM_ENV"] = "dev"
        os.environ["QUANTUM_NS"] = "quantum"
        os.environ["QUANTUM_APP_NAME"] = "obs_http_test"
        os.environ["QUANTUM_APP_VERSION"] = "0.1.0+itest"

        os.environ["QUANTUM_LOG_DIR"] = str(tmp_workspace["logs"])
        os.environ["QUANTUM_AUDIT_DIR"] = str(tmp_workspace["audit"])

        os.environ["QUANTUM_METRICS_PORT"] = str(port)
        os.environ["QUANTUM_METRICS_ADDR"] = addr

        os.environ["QUANTUM_LOG_SAMPLE_INFO"] = ""
        os.environ["QUANTUM_LOG_RATELIMIT"] = "0"

        os.environ["QUANTUM_LOG_MAX_BYTES"] = "2048"
        os.environ["QUANTUM_LOG_WARN_BYTES"] = "0"
        os.environ["QUANTUM_LOG_FSYNC"] = "0"

        os.environ["QUANTUM_TRACE_EXPORTER"] = "console"
        os.environ["QUANTUM_TRACE_SAMPLE"] = "1.0"

        # Init pipeline
        init_observability(force=True)
        try:
            log = logging.getLogger("itest.http")

            # Trigger at least one redaction via the RedactFilter
            log.info(
                "probe redact",
                extra={"attrs": {"secret": "fake_secret"}},  # pragma: allowlist secret
            )

            # Trigger rotations with a burst of large warnings
            payload = "X" * 512
            for i in range(40):
                log.warning("burst %03d %s", i, payload)

            # Poll /metrics until the pipeline is up and counters are exposed (avoids flaky sleeps)
            url = f"http://{addr}:{port}/metrics"

            def _body() -> str:
                with urllib.request.urlopen(url, timeout=2.0) as resp:
                    return resp.read().decode("utf-8", "replace")

            assert wait_until(lambda: "quantum_pipeline_up 1" in _body(), timeout_s=3.0)

            body = _body()

            # Redactions counter exposed
            assert (
                "quantum_logging_redactions_total " in body
                or "quantum_logging_redactions_total_total " in body
            ), "redactions counter not present in /metrics"

            # Rotations counter exposed
            assert (
                "quantum_logging_file_rotations_total " in body
                or "quantum_logging_file_rotations_total_total " in body
            ), "file rotations counter not present in /metrics"

        finally:
            shutdown_observability(
                close_logging=True,
                shutdown_tracing=True,
                reset_state=True,
                set_gauges_down=True,
            )
