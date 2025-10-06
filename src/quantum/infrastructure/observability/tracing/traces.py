import atexit
import logging
import os
import socket
from typing import Literal, cast

from opentelemetry.context import Context
from opentelemetry.sdk.resources import (
    DEPLOYMENT_ENVIRONMENT,
    SERVICE_INSTANCE_ID,
    SERVICE_NAME,
    SERVICE_NAMESPACE,
    SERVICE_VERSION,
    Resource,
)
from opentelemetry.sdk.trace import SpanLimits
from opentelemetry.sdk.trace import SpanProcessor as _SpanProcessor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.trace.id_generator import RandomIdGenerator
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased
from opentelemetry.trace import Span
from opentelemetry.trace import TracerProvider as TracerProviderInterface
from opentelemetry.trace import get_tracer_provider, set_tracer_provider

from quantum.shared.config.env_flags import get_bool
from quantum.shared.context.run_id import get_run_id
from quantum.shared.correlation.correlation_id import get_correlation_id

try:
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
        OTLPSpanExporter as OTLPHTTPExporter,  # type: ignore
    )

    _HAS_OTLP_HTTP = True
except ImportError:
    _HAS_OTLP_HTTP = False

try:
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
        OTLPSpanExporter as OTLPGRPCExporter,  # type: ignore
    )

    _HAS_OTLP_GRPC = True
except ImportError:
    _HAS_OTLP_GRPC = False


logger = logging.getLogger(__name__)


class TracingConfig:
    def __init__(
        self,
        service_name: str,
        environment: str,
        namespace: str,
        exporter: Literal["otlp", "console", "none"] = "console",
        sample_ratio: float = 1.0,
    ) -> None:
        self.service_name = service_name
        self.environment = environment
        self.namespace = namespace
        self.exporter = exporter
        self.sample_ratio = sample_ratio


def _resolve_instance_id() -> str:
    """
    Stable instance ID for OTel Resource:

    - QUANTUM_SERVICE_INSTANCE_ID if defined (source of truth)
    - hostname as a reasonable fallback
    """
    iid = os.getenv("QUANTUM_SERVICE_INSTANCE_ID", "").strip()
    return iid or socket.gethostname()


class _ContextEnricherProcessor(_SpanProcessor):
    def on_start(self, span: Span, parent_context: Context | None = None) -> None:
        rid = get_run_id()
        cid = get_correlation_id()
        if rid:
            span.set_attribute("quantum.run_id", rid)
        if cid:
            span.set_attribute("quantum.correlation_id", cid)

    def on_end(self, span: Span) -> None:
        pass


def init_tracing(
    cfg: TracingConfig, *, replace_existing: bool = False
) -> TracerProviderInterface:
    # Idempotence: If a provider SDK is already in place, do not reset.
    existing = get_tracer_provider()
    if isinstance(existing, TracerProvider) and not replace_existing:
        return cast(TracerProviderInterface, existing)

    # Borne le sample ratio dans [0..1]
    sr = max(0.0, min(1.0, float(cfg.sample_ratio)))

    resource = Resource.create(
        {
            SERVICE_NAME: cfg.service_name,
            SERVICE_NAMESPACE: cfg.namespace,
            DEPLOYMENT_ENVIRONMENT: cfg.environment,
            SERVICE_INSTANCE_ID: _resolve_instance_id(),
            SERVICE_VERSION: os.getenv("QUANTUM_APP_VERSION", "0.0.0"),
        }
    )

    tracer_provider = TracerProvider(
        resource=resource,
        id_generator=RandomIdGenerator(),
        sampler=ParentBased(TraceIdRatioBased(sr)),
        span_limits=SpanLimits(
            max_attributes=128,
            max_events=128,
            max_links=32,
        ),
    )

    tracer_provider.add_span_processor(_ContextEnricherProcessor())

    # Console exporter
    if cfg.exporter == "console":
        tracer_provider.add_span_processor(
            BatchSpanProcessor(
                ConsoleSpanExporter(),
                max_export_batch_size=256,
                schedule_delay_millis=500,
                max_queue_size=4096,
            )
        )

    # OTLP exporter
    active_exporter = None
    if cfg.exporter == "otlp":
        exporter, inactive_reason = _build_otlp_exporter_with_reason()
        if exporter is not None:
            tracer_provider.add_span_processor(
                BatchSpanProcessor(
                    exporter,  # type: ignore[arg-type]
                    max_export_batch_size=256,
                    schedule_delay_millis=500,
                    max_queue_size=4096,
                )
            )
            active_exporter = exporter
            _log_exporter_status(active=True)
        else:
            _log_exporter_status(active=False, reason=inactive_reason)

    set_tracer_provider(tracer_provider)
    # Expose an internal flag for init_observability (read without cross-import)
    setattr(tracer_provider, "_active_exporter", active_exporter is not None)

    # expose health metric if available (no hard dep)
    try:
        from quantum.infrastructure.observability.metrics.health import (
            tracer_exporter_active,
        )
    except ModuleNotFoundError:
        pass
    else:
        try:
            tracer_exporter_active.set(1.0 if active_exporter is not None else 0.0)
        except (ValueError, RuntimeError):
            pass

    atexit.register(tracer_provider.shutdown)

    # Expose a reference for controlled shutdown in init_observability
    try:
        import quantum.infrastructure.observability.init_observability as _init_mod
    except ModuleNotFoundError:
        pass
    else:
        _init_mod._tracer_provider_ref = cast(object, tracer_provider)

    return tracer_provider


def _build_otlp_exporter_with_reason() -> tuple[object | None, str | None]:
    """
    Constructs an OTLP HTTP or gRPC exporter.
    Returns (exporter, reason) where reason is a short string if inactive.

    Possible reasons (indicative, not exhaustive):
    - "otlp_http_package_missing"
    - "otlp_grpc_package_missing"
    - "unsupported_protocol"
    """
    protocol = os.getenv("QUANTUM_TRACE_OTLP_PROTOCOL", "http").strip().lower()
    endpoint = os.getenv("QUANTUM_TRACE_OTLP_ENDPOINT", "").strip() or (
        "http://127.0.0.1:4318" if protocol == "http" else "127.0.0.1:4317"
    )

    headers_csv = os.getenv("QUANTUM_TRACE_OTLP_HEADERS", "").strip()
    headers = {}
    if headers_csv:
        for kv in headers_csv.split(","):
            if "=" in kv:
                k, v = kv.split("=", 1)
                headers[k.strip()] = v.strip()

    timeout_ms = os.getenv("QUANTUM_TRACE_OTLP_TIMEOUT_MS", "").strip()
    try:
        timeout = int(timeout_ms) / 1000.0 if timeout_ms else None
    except ValueError:
        timeout = None

    comp = os.getenv("QUANTUM_TRACE_OTLP_COMPRESSION", "").strip().lower()
    compression = "gzip" if comp in {"gzip", "gz"} else None

    if protocol == "grpc":
        if not _HAS_OTLP_GRPC:
            return None, "otlp_grpc_package_missing"
        insecure = get_bool("QUANTUM_TRACE_OTLP_INSECURE", default=True)
        exp = OTLPGRPCExporter(
            endpoint=endpoint,
            headers=headers or None,
            timeout=timeout,
            insecure=insecure,
            compression=compression,
        )
        return exp, None

    if protocol == "http":
        if not _HAS_OTLP_HTTP:
            return None, "otlp_http_package_missing"
        exp = OTLPHTTPExporter(
            endpoint=(
                endpoint + "/v1/traces"
                if not endpoint.endswith("/v1/traces")
                else endpoint
            ),
            headers=headers or None,
            timeout=timeout,
            compression=compression,
        )
        return exp, None

    return None, "unsupported_protocol"


def _log_exporter_status(*, active: bool, reason: str | None = None) -> None:
    """
    Reporter the status of the OTLP export in a clear and non-verbal way (once at init).
    No secrets leak (we only log the protocol, the endpoint and the list of header keys).
    """
    protocol = os.getenv("QUANTUM_TRACE_OTLP_PROTOCOL", "http").strip().lower()
    endpoint = os.getenv("QUANTUM_TRACE_OTLP_ENDPOINT", "").strip() or (
        "http://127.0.0.1:4318" if protocol == "http" else "127.0.0.1:4317"
    )
    comp = os.getenv("QUANTUM_TRACE_OTLP_COMPRESSION", "").strip().lower() or "none"
    headers_csv = os.getenv("QUANTUM_TRACE_OTLP_HEADERS", "").strip()
    header_keys = []
    if headers_csv:
        for kv in headers_csv.split(","):
            if "=" in kv:
                k, _ = kv.split("=", 1)
                header_keys.append(k.strip())
    insecure = get_bool("QUANTUM_TRACE_OTLP_INSECURE", default=True)

    base = {
        "exporter": "otlp",
        "protocol": protocol,
        "endpoint": endpoint,
        "compression": comp,
        "insecure": insecure if protocol == "grpc" else None,
        "header_keys": header_keys or None,
    }

    if active:
        logger.info("OTLP exporter active", extra={"attrs": base})
    else:
        attrs = dict(base)
        attrs["reason"] = reason or "unknown"
        logger.warning("OTLP exporter configured but INACTIVE", extra={"attrs": attrs})
