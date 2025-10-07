from __future__ import annotations

import logging
from collections.abc import Callable
from contextlib import contextmanager
from typing import Any, cast

import pytest

_NumberLike = float | int | str | bytes


def _gauge_value(g: Any) -> float:
    """Simple reading of Gauge/Counter prometheus_client (isolated registry via fixture)."""
    maybe_get = getattr(getattr(g, "_value", None), "get", None)
    if not callable(maybe_get):
        return -1.0
    try:
        return float(cast(Callable[[], _NumberLike], maybe_get)())
    except Exception:
        return -1.0


@contextmanager
def _propagate(logger_name: str):
    """
    Temporarily forces propagate=True on a given logger,
    so that caplog (connected to root) captures its records.
    """
    lg = logging.getLogger(logger_name)
    old = lg.propagate
    try:
        lg.propagate = True
        yield
    finally:
        lg.propagate = old


@contextmanager
def _capture_logger(logger_name: str, level: int = logging.INFO):
    """
    Temporarily attaches a memory handler to `logger_name`.
    Returns a `records` list of captured LogRecords.
    """
    lg = logging.getLogger(logger_name)
    records: list[logging.LogRecord] = []

    class _ListHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    h = _ListHandler(level=level)
    old_level = lg.level
    lg.addHandler(h)
    lg.setLevel(min(old_level or level, level))
    try:
        yield records
    finally:
        lg.removeHandler(h)
        lg.setLevel(old_level)


def _init_then_shutdown(*, force: bool = True) -> None:
    """Starts then stops cleanly (to isolate each scenario)."""
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

            assert _gauge_value(m.pipeline_tracing_ok) == 1.0
            assert _gauge_value(m.tracer_exporter_active) == 0.0

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

        with _propagate("quantum.infrastructure.observability.tracing.traces"):
            _init_then_shutdown(force=True)

        assert _gauge_value(m.pipeline_tracing_ok) == 1.0
        assert _gauge_value(m.tracer_exporter_active) == 1.0
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

        from quantum.infrastructure.observability.metrics import health as m
        from quantum.infrastructure.observability.tracing import traces as tmod

        monkeypatch.setattr(tmod, "_HAS_OTLP_HTTP", False, raising=True)

        os.environ["QUANTUM_TRACE_EXPORTER"] = "otlp"
        os.environ["QUANTUM_TRACE_OTLP_PROTOCOL"] = "http"

        caplog.clear()
        caplog.set_level(logging.INFO)

        with _propagate("quantum.infrastructure.observability.tracing.traces"):
            with _capture_logger(
                "quantum.infrastructure.observability.tracing.traces"
            ) as recs:
                _init_then_shutdown(force=True)

        assert _gauge_value(m.pipeline_tracing_ok) == 1.0
        assert _gauge_value(m.tracer_exporter_active) == 0.0

        reasons = [
            r
            for r in recs
            if "OTLP exporter configured but INACTIVE" in (r.getMessage() or "")
        ]
        assert reasons, "Expected INACTIVE warning log"
        assert any(
            (getattr(r, "attrs", {}) or {}).get("reason") == "otlp_http_package_missing"
            or "otlp_http_package_missing" in r.getMessage()
            for r in reasons
        ), "Expected reason 'otlp_http_package_missing' in warning log"

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

        with _propagate("quantum.infrastructure.observability.tracing.traces"):
            _init_then_shutdown(force=True)

        assert _gauge_value(m.pipeline_tracing_ok) == 1.0
        assert _gauge_value(m.tracer_exporter_active) == 1.0

    def test_otlp_grpc_inactive_when_pkg_missing(
        self, tmp_workspace, monkeypatch, caplog
    ):
        """
        export=otlp, protocol=grpc, package missing → inactive=0.0 and log reason='otlp_grpc_package_missing'.
        """
        import os

        from quantum.infrastructure.observability.metrics import health as m
        from quantum.infrastructure.observability.tracing import traces as tmod

        monkeypatch.setattr(tmod, "_HAS_OTLP_GRPC", False, raising=True)

        os.environ["QUANTUM_TRACE_EXPORTER"] = "otlp"
        os.environ["QUANTUM_TRACE_OTLP_PROTOCOL"] = "grpc"
        os.environ["QUANTUM_TRACE_OTLP_INSECURE"] = "1"

        caplog.clear()
        caplog.set_level(logging.INFO)

        with _propagate("quantum.infrastructure.observability.tracing.traces"):
            with _capture_logger(
                "quantum.infrastructure.observability.tracing.traces"
            ) as recs:
                _init_then_shutdown(force=True)

        assert _gauge_value(m.pipeline_tracing_ok) == 1.0
        assert _gauge_value(m.tracer_exporter_active) == 0.0

        reasons = [
            r
            for r in recs
            if "OTLP exporter configured but INACTIVE" in (r.getMessage() or "")
        ]
        assert reasons, "Expected INACTIVE warning log"
        assert any(
            (getattr(r, "attrs", {}) or {}).get("reason") == "otlp_grpc_package_missing"
            or "otlp_grpc_package_missing" in r.getMessage()
            for r in reasons
        ), "Expected reason 'otlp_grpc_package_missing' in warning log"

    def test_otlp_unsupported_protocol_is_inactive(self, tmp_workspace, caplog):
        """
        exporter=otlp, protocol inconnu → inactive=0.0
        et log reason='unsupported_protocol'.
        """
        import os

        from quantum.infrastructure.observability.metrics import health as m

        os.environ["QUANTUM_TRACE_EXPORTER"] = "otlp"
        os.environ["QUANTUM_TRACE_OTLP_PROTOCOL"] = "ws"  # invalide

        caplog.clear()
        caplog.set_level(logging.INFO)

        with _propagate("quantum.infrastructure.observability.tracing.traces"):
            with _capture_logger(
                "quantum.infrastructure.observability.tracing.traces"
            ) as recs:
                _init_then_shutdown(force=True)

        assert _gauge_value(m.pipeline_tracing_ok) == 1.0
        assert _gauge_value(m.tracer_exporter_active) == 0.0

        reasons = [
            r
            for r in recs
            if "OTLP exporter configured but INACTIVE" in (r.getMessage() or "")
        ]
        assert reasons, "Expected INACTIVE warning log"
        assert any(
            (getattr(r, "attrs", {}) or {}).get("reason") == "unsupported_protocol"
            or "unsupported_protocol" in r.getMessage()
            for r in reasons
        ), "Expected reason 'unsupported_protocol' in warning log"

    def test_otlp_init_failure_triggers_fallback(
        self, tmp_workspace, monkeypatch, caplog
    ):
        """
        If init_tracing throws an exception (e.g., an OTLP constructor crashes),
        init_observability applies the fallback: exporter=none, sample_ratio=0.0

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

        with _propagate("quantum.infrastructure.observability.tracing.traces"):
            with _propagate("quantum.infrastructure.observability.init_observability"):
                with _capture_logger(
                    "quantum.infrastructure.observability.init_observability"
                ) as recs:
                    init_observability(force=True)
                    try:
                        assert _gauge_value(m.pipeline_tracing_ok) == 1.0
                        assert _gauge_value(m.tracer_exporter_active) == 0.0
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
