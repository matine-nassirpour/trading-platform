from __future__ import annotations

import logging

import pytest

from tests.support.logging_utils import capture_logger, counter_value, propagate_logger

# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Helpers                                                                     │
# ╰─────────────────────────────────────────────────────────────────────────────╯


def _init_then_shutdown(*, force: bool = True) -> None:
    """Start then stop cleanly (isolate each scenario)."""
    from quantum.infrastructure.observability.bootstrap.init_manager import (
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
    log_name: str = "quantum.infrastructure.observability.tracing.provider",
) -> None:
    """
    Common assertion for 'inactive' scenarios:
      - pipeline_tracing_ok == 1.0
      - tracing_exporter_status == 0.0
      - warning log "OTLP exporter configured but INACTIVE" containing the expected reason
    """
    from quantum.infrastructure.observability.bootstrap.health_registry import (
        get_health_registry,
    )
    from quantum.infrastructure.observability.metrics.collectors import (
        health_collector as m,
    )

    caplog.clear()
    caplog.set_level(logging.INFO)

    registry = get_health_registry()

    with propagate_logger(log_name):
        with capture_logger(log_name) as recs:
            _init_then_shutdown(force=True)

    assert (
        registry.pipeline_tracing_ok._value.get() == 1.0
    ), "Tracing pipeline should init (even inactive)"
    assert (
        counter_value(m.tracing_exporter_status) == 0.0
    ), "Exporter should be inactive"

    reasons = [r for r in recs if "OTLP exporter inactive" in (r.getMessage() or "")]
    assert reasons, "Expected INACTIVE warning log"
    assert any(
        reason_expected in ((getattr(r, "attrs", {}) or {}).get("reason") or "")
        or reason_expected in (r.getMessage() or "")
        for r in reasons
    ), f"Expected reason substring {reason_expected!r} in warning log"


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Tests                                                                       │
# ╰─────────────────────────────────────────────────────────────────────────────╯


@pytest.mark.validation
@pytest.mark.usefixtures("no_rate_limit_no_sampling")
class TestOTLPExporterSelection:
    def test_console_and_none_exporters_are_inactive(self, tmp_workspace, caplog):
        """
        exporter=console|none → tracing_exporter_status == 0.0, pipeline_tracing_ok == 1.0
        (console active, none explicit).
        """
        import os

        from quantum.infrastructure.observability.bootstrap.health_registry import (
            get_health_registry,
        )
        from quantum.infrastructure.observability.metrics.collectors import (
            health_collector as m,
        )

        registry = get_health_registry()

        for exp in ("console", "none"):
            caplog.clear()
            caplog.set_level(logging.INFO)

            os.environ["QUANTUM_TRACE_EXPORTER"] = exp
            os.environ["QUANTUM_TRACE_OTLP_PROTOCOL"] = "http"

            _init_then_shutdown(force=True)

            assert registry.pipeline_tracing_ok._value.get() == 1.0
            assert counter_value(m.tracing_exporter_status) == 0.0

    def test_otlp_http_active_when_pkg_present(
        self, tmp_workspace, monkeypatch, caplog
    ):
        """
        exporter=otlp, protocol=http, package present → active=1.0 (no warning).
        """
        import os
        import sys
        import types

        from quantum.infrastructure.observability.bootstrap.health_registry import (
            get_health_registry,
        )
        from quantum.infrastructure.observability.metrics.collectors import (
            health_collector as m,
        )

        fake_http_module = types.ModuleType(
            "opentelemetry.exporter.otlp.proto.http.trace_exporter"
        )

        class DummyExporter:
            def __init__(self, *args, **kwargs):
                pass

        fake_http_module.OTLPSpanExporter = DummyExporter

        monkeypatch.setitem(
            sys.modules,
            "opentelemetry.exporter.otlp.proto.http.trace_exporter",
            fake_http_module,
        )

        os.environ["QUANTUM_TRACE_EXPORTER"] = "otlp"
        os.environ["QUANTUM_TRACE_OTLP_PROTOCOL"] = "http"

        caplog.clear()
        caplog.set_level(logging.INFO)

        registry = get_health_registry()

        with propagate_logger("quantum.infrastructure.observability.tracing.traces"):
            _init_then_shutdown(force=True)

        assert registry.pipeline_tracing_ok._value.get() == 1.0
        assert counter_value(m.tracing_exporter_status) == 1.0
        assert not any("OTLP exporter inactive" in r.message for r in caplog.records)

    def test_otlp_http_inactive_when_pkg_missing(
        self, tmp_workspace, monkeypatch, caplog
    ):
        """
        exporter=otlp, protocol=http, missing package → inactive=0.0
        and inactivity log with reason='otlp_package_missing'.
        """
        import builtins
        import os
        import sys

        for mod in list(sys.modules):
            if mod.startswith("opentelemetry.exporter.otlp.proto.http"):
                sys.modules.pop(mod, None)

        original_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name.startswith("opentelemetry.exporter.otlp.proto.http.trace_exporter"):
                raise ImportError("synthetic missing package")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)

        os.environ["QUANTUM_TRACE_EXPORTER"] = "otlp"
        os.environ["QUANTUM_TRACE_OTLP_PROTOCOL"] = "http"

        _assert_inactive_with_reason(caplog, reason_expected="otlp_package_missing")

    def test_otlp_grpc_active_when_pkg_present(
        self, tmp_workspace, monkeypatch, caplog
    ):
        """
        exporter=otlp, protocol=grpc, package present → active=1.0.
        """
        import os
        import sys
        import types

        from quantum.infrastructure.observability.bootstrap.health_registry import (
            get_health_registry,
        )
        from quantum.infrastructure.observability.metrics.collectors import (
            health_collector as m,
        )

        fake_grpc_module = types.ModuleType(
            "opentelemetry.exporter.otlp.proto.grpc.trace_exporter"
        )

        class DummyExporter:
            def __init__(self, *args, **kwargs):
                pass

        fake_grpc_module.OTLPSpanExporter = DummyExporter

        monkeypatch.setitem(
            sys.modules,
            "opentelemetry.exporter.otlp.proto.grpc.trace_exporter",
            fake_grpc_module,
        )

        os.environ["QUANTUM_TRACE_EXPORTER"] = "otlp"
        os.environ["QUANTUM_TRACE_OTLP_PROTOCOL"] = "grpc"
        os.environ["QUANTUM_TRACE_OTLP_INSECURE"] = "1"

        caplog.clear()
        caplog.set_level(logging.INFO)

        registry = get_health_registry()

        with propagate_logger("quantum.infrastructure.observability.tracing.traces"):
            _init_then_shutdown(force=True)

        assert registry.pipeline_tracing_ok._value.get() == 1.0
        assert counter_value(m.tracing_exporter_status) == 1.0

    def test_otlp_grpc_inactive_when_pkg_missing(
        self, tmp_workspace, monkeypatch, caplog
    ):
        """
        exporter=otlp, protocol=grpc, package missing → inactive=0.0
        and log reason='otlp_grpc_package_missing'.
        """
        import builtins
        import os
        import sys

        for mod in list(sys.modules):
            if mod.startswith("opentelemetry.exporter.otlp.proto.grpc"):
                sys.modules.pop(mod, None)

        original_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name.startswith("opentelemetry.exporter.otlp.proto.grpc.trace_exporter"):
                raise ImportError("synthetic missing grpc exporter")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)

        os.environ["QUANTUM_TRACE_EXPORTER"] = "otlp"
        os.environ["QUANTUM_TRACE_OTLP_PROTOCOL"] = "grpc"
        os.environ["QUANTUM_TRACE_OTLP_INSECURE"] = "1"

        _assert_inactive_with_reason(caplog, reason_expected="otlp_package_missing")

    def test_otlp_unsupported_protocol_defaults_to_http(self, tmp_workspace, caplog):
        """
        exporter=otlp, protocol unsupported ('ws') → normalized to 'http', exporter active.
        """
        import os

        from quantum.infrastructure.observability.metrics.collectors import (
            health_collector as m,
        )

        os.environ["QUANTUM_TRACE_EXPORTER"] = "otlp"
        os.environ["QUANTUM_TRACE_OTLP_PROTOCOL"] = "ws"  # invalid literal

        caplog.set_level(logging.WARNING)
        _init_then_shutdown(force=True)

        # Exporter should be active, since 'ws' defaulted to 'http'
        assert counter_value(m.tracing_exporter_status) == 1.0
        assert any(
            "Unsupported OTLP protocol 'ws'" in r.message for r in caplog.records
        )

    def test_otlp_init_failure_triggers_fallback(
        self, tmp_workspace, monkeypatch, caplog
    ):
        """
        If init_tracing raises (e.g., OTLP constructor crashes), init_observability
        falls back to exporter=none, sample_ratio=0.0.

        - pipeline_tracing_ok == 1.0
        - tracing_exporter_status == 0.0
        - warning "Tracing fallback activated..."
        """
        import os

        from quantum.infrastructure.observability.bootstrap.health_registry import (
            get_health_registry,
        )
        from quantum.infrastructure.observability.bootstrap.init_manager import (
            init_observability,
            shutdown_observability,
        )
        from quantum.infrastructure.observability.metrics.collectors import (
            health_collector as m,
        )
        from quantum.infrastructure.observability.tracing import provider as tmod

        os.environ["QUANTUM_TRACE_EXPORTER"] = "otlp"
        os.environ["QUANTUM_TRACE_OTLP_PROTOCOL"] = "http"

        def _boom(tracing_settings) -> tuple[object | None, str | None]:
            raise RuntimeError("synthetic exporter build failure")

        monkeypatch.setattr(tmod, "_build_otlp_exporter", _boom, raising=True)

        caplog.clear()
        caplog.set_level(logging.INFO)

        registry = get_health_registry()

        with propagate_logger("quantum.infrastructure.observability.tracing.provider"):
            with propagate_logger(
                "quantum.infrastructure.observability.bootstrap.lifecycle"
            ):
                with capture_logger(
                    "quantum.infrastructure.observability.bootstrap.lifecycle"
                ) as recs:
                    init_observability(force=True)
                    try:
                        assert registry.pipeline_tracing_ok._value.get() == 1.0
                        assert counter_value(m.tracing_exporter_status) == 0.0
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
