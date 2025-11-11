import atexit
import logging
import socket

from typing import Any, cast

from opentelemetry import trace as _trace
from opentelemetry.context import Context
from opentelemetry.exporter.otlp.proto.http import Compression
from opentelemetry.sdk.resources import (
    DEPLOYMENT_ENVIRONMENT,
    SERVICE_INSTANCE_ID,
    SERVICE_NAME,
    SERVICE_NAMESPACE,
    SERVICE_VERSION,
    Resource,
)
from opentelemetry.sdk.trace import (
    ReadableSpan,
    SpanLimits,
    SpanProcessor,
    TracerProvider,
)
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SpanExporter,
)
from opentelemetry.sdk.trace.id_generator import RandomIdGenerator
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased
from opentelemetry.trace import Span, Tracer
from opentelemetry.trace import TracerProvider as TracerProviderInterface
from opentelemetry.trace import get_tracer_provider, set_tracer_provider

from quantum.infrastructure.config.models.core import CoreSettings
from quantum.infrastructure.config.models.tracing import TracingSettings
from quantum.infrastructure.observability.context.run_id import get_run_id
from quantum.infrastructure.observability.tracing.correlation.correlation_id import (
    get_correlation_id,
)

logger = logging.getLogger(__name__)
_ATEXIT_REGISTERED: bool = False


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Lifecycle Management                                                       │
# ╰────────────────────────────────────────────────────────────────────────────╯
def _shutdown_provider_safely() -> None:
    """Gracefully shutdown the current tracer provider (safe for multiple calls)."""
    try:
        provider = get_tracer_provider()
        shutdown = getattr(provider, "shutdown", None)
        if callable(shutdown):
            shutdown()
    except Exception as exc:
        logger.debug(f"Tracer provider shutdown at exit failed: {exc}")


def _ensure_atexit_registered() -> None:
    """Ensure provider shutdown is registered exactly once."""
    global _ATEXIT_REGISTERED
    if _ATEXIT_REGISTERED:
        return
    try:
        atexit.register(_shutdown_provider_safely)
        _ATEXIT_REGISTERED = True
    except Exception as exc:
        logger.debug(f"Failed to register atexit tracer shutdown: {exc}")


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Context Processor                                                          │
# ╰────────────────────────────────────────────────────────────────────────────╯
class _ContextEnricherProcessor(SpanProcessor):
    """Injects run_id and correlation_id into every span at start time."""

    def on_start(self, span: Span, parent_context: Context | None = None) -> None:
        try:
            rid = get_run_id()
            cid = get_correlation_id()
            if rid:
                span.set_attribute("quantum.run_id", rid)
            if cid:
                span.set_attribute("quantum.correlation_id", cid)
        except Exception as exc:
            logger.debug(f"Context enrichment failed: {exc}")

    def on_end(self, span: ReadableSpan) -> None:
        pass

    def shutdown(self) -> None:
        """No cleanup needed."""
        return

    def force_flush(self, timeout_millis: int | None = None) -> bool:
        """No buffered state; always succeeds."""
        return True


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ OTLP Exporter Builder                                                      │
# ╰────────────────────────────────────────────────────────────────────────────╯
def _parse_otlp_headers(headers_csv: str | None) -> dict[str, str]:
    headers: dict[str, str] = {}
    if not headers_csv:
        return headers

    for kv in headers_csv.split(","):
        if "=" in kv:
            k, v = kv.split("=", 1)
            headers[k.strip()] = v.strip()

    return headers


def _create_http_exporter(
    endpoint: str, headers: dict[str, str], timeout: float, compression: Any
) -> SpanExporter:
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
        OTLPSpanExporter as OTLPHTTPExporter,
    )

    if not endpoint.endswith("/v1/traces"):
        endpoint = endpoint.rstrip("/") + "/v1/traces"

    return OTLPHTTPExporter(
        endpoint=endpoint,
        headers=headers or None,
        timeout=timeout,
        compression=compression,
    )


def _create_grpc_exporter(
    endpoint: str,
    headers: dict[str, str],
    timeout: float,
    insecure: bool,
    compression: Any,
) -> SpanExporter:
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
        OTLPSpanExporter as OTLPGRPCExporter,
    )

    return OTLPGRPCExporter(
        endpoint=endpoint,
        headers=headers or None,
        timeout=timeout,
        insecure=insecure,
        compression=compression,
    )


def _build_otlp_exporter(
    tracing_settings: TracingSettings,
) -> tuple[Any | None, str | None]:
    """
    Build an OTLP exporter based on TelemetrySettings.
    Returns (exporter, reason) where reason is present if inactive.
    """
    protocol = tracing_settings.quantum_trace_otlp_protocol
    endpoint = tracing_settings.quantum_trace_otlp_endpoint
    timeout = tracing_settings.quantum_trace_otlp_timeout_ms / 1000.0
    insecure = tracing_settings.quantum_trace_otlp_insecure
    headers = _parse_otlp_headers(tracing_settings.quantum_trace_otlp_headers)
    compression = (
        None
        if tracing_settings.quantum_trace_otlp_compression == "none"
        else Compression.Gzip
    )

    try:
        if protocol == "http":
            return _create_http_exporter(endpoint, headers, timeout, compression), None

        if protocol == "grpc":
            return (
                _create_grpc_exporter(
                    endpoint, headers, timeout, insecure, compression
                ),
                None,
            )

        return None, f"unsupported_protocol:{protocol}"

    except ImportError as exc:
        return None, f"otlp_package_missing:{exc.__class__.__name__}"
    except Exception as exc:
        return None, f"otlp_exporter_error:{exc}"


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ TracerProvider creation pipeline                                           │
# ╰────────────────────────────────────────────────────────────────────────────╯
def _create_tracer_provider(
    core_settings: CoreSettings, tracing_settings: TracingSettings
) -> TracerProvider:
    sample_ratio = max(0.0, min(1.0, float(tracing_settings.quantum_trace_sample)))
    resource = Resource.create(
        {
            SERVICE_NAME: core_settings.quantum_app_name,
            SERVICE_VERSION: core_settings.quantum_app_version,
            SERVICE_NAMESPACE: core_settings.quantum_ns,
            DEPLOYMENT_ENVIRONMENT: core_settings.quantum_env,
            SERVICE_INSTANCE_ID: (
                core_settings.quantum_instance_id or socket.gethostname()
            ),
        }
    )
    provider = TracerProvider(
        resource=resource,
        id_generator=RandomIdGenerator(),
        sampler=ParentBased(TraceIdRatioBased(sample_ratio)),
        span_limits=SpanLimits(max_attributes=128, max_events=128, max_links=32),
    )
    provider.add_span_processor(_ContextEnricherProcessor())
    return provider


def _attach_exporter(
    provider: TracerProvider, tracing_settings: TracingSettings
) -> tuple[Any | None, str | None]:
    """Attach the proper exporter (console, otlp, or none) to the provider."""
    name = tracing_settings.quantum_trace_exporter
    if name == "console":
        provider.add_span_processor(
            BatchSpanProcessor(
                ConsoleSpanExporter(),
                max_export_batch_size=256,
                schedule_delay_millis=500,
                max_queue_size=4096,
            )
        )
        return None, "exporter=console"
    if name == "otlp":
        exporter, reason = _build_otlp_exporter(tracing_settings)
        if exporter:
            provider.add_span_processor(
                BatchSpanProcessor(
                    exporter,
                    max_export_batch_size=256,
                    schedule_delay_millis=500,
                    max_queue_size=4096,
                )
            )
        return exporter, reason
    if name == "none":
        return None, "exporter=none"
    return None, f"unsupported_exporter:{name}"


def _finalize_provider(
    provider: TracerProvider,
    tracing_settings: TracingSettings,
    active_exporter: Any | None,
    inactive_reason: str | None,
) -> None:
    """Set provider globally, log exporter state, and update health metric."""
    set_tracer_provider(provider)
    _log_exporter_status(active_exporter, tracing_settings, inactive_reason)

    try:
        from quantum.infrastructure.observability.metrics.collectors.health_collector import (
            tracing_exporter_status,
        )
    except ModuleNotFoundError:
        logger.debug(
            "Health metrics module not found; skipping exporter activity metric."
        )
    else:
        try:
            tracing_exporter_status.set(1.0 if active_exporter else 0.0)
        except (ValueError, RuntimeError, AttributeError) as exc:
            logger.debug(f"Unable to update tracer exporter metric: {exc}")

    try:
        from quantum.infrastructure.observability.bootstrap.state import (
            set_tracer_provider as tp,
        )

        tp(provider)
    except Exception as exc:
        logger.debug(f"Failed to register tracer provider globally: {exc}")

    _ensure_atexit_registered()


def init_tracing(
    core_settings: CoreSettings,
    tracing_settings: TracingSettings,
    replace_existing: bool = False,
) -> TracerProviderInterface:
    """Initialize the OpenTelemetry TracerProvider."""
    existing = get_tracer_provider()
    if isinstance(existing, TracerProvider) and not replace_existing:
        _ensure_atexit_registered()
        return cast(TracerProviderInterface, existing)

    provider = _create_tracer_provider(core_settings, tracing_settings)
    exporter, reason = _attach_exporter(provider, tracing_settings)
    _finalize_provider(provider, tracing_settings, exporter, reason)
    return provider


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Logging Helpers                                                            │
# ╰────────────────────────────────────────────────────────────────────────────╯
def _log_exporter_status(
    active_exporter: Any | None,
    tracing_settings: TracingSettings,
    inactive_reason: str | None,
) -> None:
    """
    Report the status of the OTLP/Console exporter.
    No sensitive data is logged — only structural metadata.
    """
    base: dict[str, Any] = {
        "protocol": tracing_settings.quantum_trace_otlp_protocol,
        "compression": tracing_settings.quantum_trace_otlp_compression,
        "insecure": tracing_settings.quantum_trace_otlp_insecure,
    }

    headers_preview: list[str] = []
    if tracing_settings.quantum_trace_otlp_headers:
        for kv in tracing_settings.quantum_trace_otlp_headers.split(","):
            if "=" in kv:
                k, _ = kv.split("=", 1)
                headers_preview.append(k.strip())
    if headers_preview:
        base["header_keys"] = headers_preview

    if active_exporter:
        logger.info("OTLP exporter active", extra={"attrs": base})
    else:
        attrs = dict(base)
        attrs["reason"] = inactive_reason or "unknown"
        logger.warning("OTLP exporter inactive", extra={"attrs": attrs})


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Public API                                                                 │
# ╰────────────────────────────────────────────────────────────────────────────╯
def get_tracer(component: str, version: str = "1.0.0") -> Tracer:
    """
    Return a canonical tracer for the given component.
    Example: get_tracer("infra.execution.mt5")
    """
    return _trace.get_tracer(f"quantum.{component}", version)
