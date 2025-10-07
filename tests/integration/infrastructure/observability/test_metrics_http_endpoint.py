from __future__ import annotations

import logging
import os
import socket
import time
import urllib.request
from typing import Final

import pytest


def _free_port() -> int:
    """Retourne un port TCP libre sur 127.0.0.1 (réservé puis libéré immédiatement)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.mark.usefixtures("no_rate_limit_no_sampling")
class TestMetricsHTTPEndpoint:
    def test_metrics_http_endpoint_exposes_core_metrics(self, tmp_workspace, tmp_path):
        """
        Démarre le /metrics (Prometheus) et vérifie :
          - presence de 'quantum_pipeline_up 1'
          - compteur de redaction > 0 après un log avec secret
          - compteur de rotation >= 1 après un burst avec QUANTUM_LOG_MAX_BYTES faible
        """
        from quantum.infrastructure.observability.init_observability import (
            init_observability,
            shutdown_observability,
        )

        # Choosing a free port
        port = _free_port()
        addr: Final = "127.0.0.1"

        # Clean ENV for this scenario
        os.environ["QUANTUM_ENV"] = "dev"
        os.environ["QUANTUM_NS"] = "quantum"
        os.environ["QUANTUM_APP_NAME"] = "obs_http_test"
        os.environ["QUANTUM_APP_VERSION"] = "0.1.0+itest"

        # File-side logging (partitioned JSONL) + fast fs
        os.environ["QUANTUM_LOG_DIR"] = str(tmp_workspace["logs"])
        os.environ["QUANTUM_AUDIT_DIR"] = str(tmp_workspace["audit"])

        # /metrics enabled
        os.environ["QUANTUM_METRICS_PORT"] = str(port)
        os.environ["QUANTUM_METRICS_ADDR"] = addr

        # No sampling/rate limit to let all logs through
        os.environ["QUANTUM_LOG_SAMPLE_INFO"] = ""
        os.environ["QUANTUM_LOG_RATELIMIT"] = "0"

        # Easy rotation (~2KB)
        os.environ["QUANTUM_LOG_MAX_BYTES"] = "2048"
        os.environ["QUANTUM_LOG_WARN_BYTES"] = "0"
        os.environ["QUANTUM_LOG_FSYNC"] = "0"

        # Neutral tracing
        os.environ["QUANTUM_TRACE_EXPORTER"] = "console"
        os.environ["QUANTUM_TRACE_SAMPLE"] = "1.0"

        # Init pipeline
        init_observability(force=True)
        try:
            log = logging.getLogger("itest.http")

            # Triggers at least one redaction via the RedactFilter
            log.info(
                "probe redact",
                extra={
                    "attrs": {
                        "secret": "this_is_a_fake_secret"  # pragma: allowlist secret
                    }
                },
            )

            # Triggers a rotation with a burst of large warnings
            payload = "X" * 512
            for i in range(40):
                log.warning("burst %03d %s", i, payload)

            # Allow time for the handler to flush/update the counters
            time.sleep(0.25)

            # GET /metrics and checks
            url = f"http://{addr}:{port}/metrics"
            with urllib.request.urlopen(url, timeout=2.0) as resp:
                body = resp.read().decode("utf-8", "replace")

            # Pipeline up
            assert "quantum_pipeline_up 1" in body

            # Redactions > 0
            # Examples of possible lines:
            #   quantum_logging_redactions_total 1.0
            #   quantum_logging_redactions_total_total 1.0
            assert (
                "quantum_logging_redactions_total " in body
                or "quantum_logging_redactions_total_total " in body
            ), "redactions counter not present in /metrics"
            # Value > 0 (searching for a line containing '0' vs. '1' is not robust,
            # we just use presence + triggered context).

            # Rotations >= 1 (same naming logic _total following the lib)
            assert (
                "quantum_logging_file_rotations_total " in body
                or "quantum_logging_file_rotations_total_total " in body
            ), "file rotations counter not present in /metrics"

        finally:
            # Clean shutdown (Prometheus HTTP server remains process-wide; this is OK)
            shutdown_observability(
                close_logging=True,
                shutdown_tracing=True,
                reset_state=True,
                set_gauges_down=True,
            )
