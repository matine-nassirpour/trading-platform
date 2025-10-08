from __future__ import annotations

import logging

import pytest

from tests.support.logging_utils import capture_logger, counter_value, propagate_logger

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


def _init_then_shutdown(*, force: bool = True) -> None:
    """Start then stop cleanly (isolate each scenario)."""
    from quantum.infrastructure.observability.init_observability import (
        init_observability,
        shutdown_observability,
    )

    init_observability(force=force)
    shutdown_observability(
        close_logging=True,
        shutdown_tracing=True,
        reset_state=True,
        set_gauges_down=True,
    )


def _assert_inactive_with_reason(
    caplog: pytest.LogCaptureFixture,
    *,
    reason_expected: str,
    log_name: str = "quantum.infrastructure.observability.tracing.traces",
) -> None:
    """
    Common assertion for 'inactive' scenarios:
      - pipeline_tracing_ok == 1.0
      - tracer_exporter_active == 0.0
      - warning log "OTLP exporter configured but INACTIVE" containing the expected reason
    """
    from quantum.infrastructure.observability.metrics import health as m

    caplog.clear()
    caplog.set_level(logging.INFO)

    with propagate_logger(log_name):
        with capture_logger(log_name) as recs:
            _init_then_shutdown(force=True)

    assert counter_value(m.pipeline_tracing_ok) == 1.0
    assert counter_value(m.tracer_exporter_active) == 0.0

    reasons = [
        r
        for r in recs
        if "OTLP exporter configured but INACTIVE" in (r.getMessage() or "")
    ]
    assert reasons, "Expected INACTIVE warning log"
    assert any(
        (getattr(r, "attrs", {}) or {}).get("reason") == reason_expected
        or reason_expected in r.getMessage()
        for r in reasons
    ), f"Expected reason {reason_expected!r} in warning log"


# ──────────────────────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.usefixtures("no_rate_limit_no_sampling")
class TestOTLPExporterSelection:
    def test_console_and_none_exporters_are_inactive(self, tmp_workspace, caplog):
        """
        exporter=console|none → tracer_exporter_active == 0.0, pipeline_tracing_ok == 1.0
        (console active, none explicit).
        """
        import os

        from quantum.infrastructure.observability.metrics import health as m

        for exp in ("console", "none"):
            caplog.clear()
            caplog.set_level(logging.INFO)

            os.environ["QUANTUM_TRACE_EXPORTER"] = exp
            os.environ["QUANTUM_TRACE_OTLP_PROTOCOL"] = "http"

            _init_then_shutdown(force=True)

            assert counter_value(m.pipeline_tracing_ok) == 1.0
            assert counter_value(m.tracer_exporter_active) == 0.0

    def test_otlp_http_active_when_pkg_present(
        self, tmp_workspace, monkeypatch, caplog
    ):
        """
        exporter=otlp, protocol=http, package present → active=1.0 (no warning).
        """
        import os

        from quantum.infrastructure.observability.metrics import health as m
        from quantum.infrastructure.observability.tracing import traces as tmod

        monkeypatch.setattr(tmod, "_HAS_OTLP_HTTP", True, raising=True)

        os.environ["QUANTUM_TRACE_EXPORTER"] = "otlp"
        os.environ["QUANTUM_TRACE_OTLP_PROTOCOL"] = "http"

        caplog.clear()
        caplog.set_level(logging.INFO)

        with propagate_logger("quantum.infrastructure.observability.tracing.traces"):
            _init_then_shutdown(force=True)

        assert counter_value(m.pipeline_tracing_ok) == 1.0
        assert counter_value(m.tracer_exporter_active) == 1.0
        assert not any(
            "OTLP exporter configured but INACTIVE" in r.message for r in caplog.records
        )

    def test_otlp_http_inactive_when_pkg_missing(
        self, tmp_workspace, monkeypatch, caplog
    ):
        """
        exporter=otlp, protocol=http, missing package → inactive=0.0 and inactivity log with reason='otlp_http_package_missing'.
        """
        import os

        from quantum.infrastructure.observability.tracing import traces as tmod

        monkeypatch.setattr(tmod, "_HAS_OTLP_HTTP", False, raising=True)

        os.environ["QUANTUM_TRACE_EXPORTER"] = "otlp"
        os.environ["QUANTUM_TRACE_OTLP_PROTOCOL"] = "http"

        _assert_inactive_with_reason(
            caplog, reason_expected="otlp_http_package_missing"
        )

    def test_otlp_grpc_active_when_pkg_present(
        self, tmp_workspace, monkeypatch, caplog
    ):
        """
        exporter=otlp, protocol=grpc, package present → active=1.0.
        """
        import os

        from quantum.infrastructure.observability.metrics import health as m
        from quantum.infrastructure.observability.tracing import traces as tmod

        monkeypatch.setattr(tmod, "_HAS_OTLP_GRPC", True, raising=True)

        os.environ["QUANTUM_TRACE_EXPORTER"] = "otlp"
        os.environ["QUANTUM_TRACE_OTLP_PROTOCOL"] = "grpc"
        os.environ["QUANTUM_TRACE_OTLP_INSECURE"] = "1"

        caplog.clear()
        caplog.set_level(logging.INFO)

        with propagate_logger("quantum.infrastructure.observability.tracing.traces"):
            _init_then_shutdown(force=True)

        assert counter_value(m.pipeline_tracing_ok) == 1.0
        assert counter_value(m.tracer_exporter_active) == 1.0

    def test_otlp_grpc_inactive_when_pkg_missing(
        self, tmp_workspace, monkeypatch, caplog
    ):
        """
        exporter=otlp, protocol=grpc, package missing → inactive=0.0 and log reason='otlp_grpc_package_missing'.
        """
        import os

        from quantum.infrastructure.observability.tracing import traces as tmod

        monkeypatch.setattr(tmod, "_HAS_OTLP_GRPC", False, raising=True)

        os.environ["QUANTUM_TRACE_EXPORTER"] = "otlp"
        os.environ["QUANTUM_TRACE_OTLP_PROTOCOL"] = "grpc"
        os.environ["QUANTUM_TRACE_OTLP_INSECURE"] = "1"

        _assert_inactive_with_reason(
            caplog, reason_expected="otlp_grpc_package_missing"
        )

    def test_otlp_unsupported_protocol_is_inactive(self, tmp_workspace, caplog):
        """
        exporter=otlp, unknown protocol → inactive=0.0 and log reason='unsupported_protocol'.
        """
        import os

        os.environ["QUANTUM_TRACE_EXPORTER"] = "otlp"
        os.environ["QUANTUM_TRACE_OTLP_PROTOCOL"] = "ws"  # invalid

        _assert_inactive_with_reason(caplog, reason_expected="unsupported_protocol")

    def test_otlp_init_failure_triggers_fallback(
        self, tmp_workspace, monkeypatch, caplog
    ):
        """
        If init_tracing raises (e.g., OTLP constructor crashes), init_observability
        falls back to exporter=none, sample_ratio=0.0.

        - pipeline_tracing_ok == 1.0
        - tracer_exporter_active == 0.0
        - warning "Tracing fallback activated..."
        """
        import os

        from quantum.infrastructure.observability.init_observability import (
            init_observability,
            shutdown_observability,
        )
        from quantum.infrastructure.observability.metrics import health as m
        from quantum.infrastructure.observability.tracing import traces as tmod

        os.environ["QUANTUM_TRACE_EXPORTER"] = "otlp"
        os.environ["QUANTUM_TRACE_OTLP_PROTOCOL"] = "http"

        def _boom() -> tuple[object | None, str | None]:
            raise RuntimeError("synthetic exporter build failure")

        monkeypatch.setattr(
            tmod, "_build_otlp_exporter_with_reason", _boom, raising=True
        )

        caplog.clear()
        caplog.set_level(logging.INFO)

        with propagate_logger("quantum.infrastructure.observability.tracing.traces"):
            with propagate_logger(
                "quantum.infrastructure.observability.init_observability"
            ):
                with capture_logger(
                    "quantum.infrastructure.observability.init_observability"
                ) as recs:
                    init_observability(force=True)
                    try:
                        assert counter_value(m.pipeline_tracing_ok) == 1.0
                        assert counter_value(m.tracer_exporter_active) == 0.0
                        assert any(
                            "Tracing fallback activated" in (r.getMessage() or "")
                            for r in recs
                        ), "Expected fallback warning"
                    finally:
                        shutdown_observability(
                            close_logging=True,
                            shutdown_tracing=True,
                            reset_state=True,
                            set_gauges_down=True,
                        )
