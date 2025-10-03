import atexit
import os
import socket
from typing import Literal, cast

from opentelemetry.sdk.resources import (
    DEPLOYMENT_ENVIRONMENT,
    SERVICE_INSTANCE_ID,
    SERVICE_NAME,
    SERVICE_NAMESPACE,
    SERVICE_VERSION,
    Resource,
)
from opentelemetry.sdk.trace import SpanLimits, TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.trace.id_generator import RandomIdGenerator
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased
from opentelemetry.trace import TracerProvider as TracerProviderInterface
from opentelemetry.trace import set_tracer_provider

try:
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
        OTLPSpanExporter as OTLPHTTPExporter,  # type: ignore
    )

    _HAS_OTLP_HTTP = True
except Exception:
    _HAS_OTLP_HTTP = False

try:
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
        OTLPSpanExporter as OTLPGRPCExporter,  # type: ignore
    )

    _HAS_OTLP_GRPC = True
except Exception:
    _HAS_OTLP_GRPC = False


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


def init_tracing(cfg: TracingConfig) -> TracerProviderInterface:
    resource = Resource.create(
        {
            SERVICE_NAME: cfg.service_name,
            SERVICE_NAMESPACE: cfg.namespace,
            DEPLOYMENT_ENVIRONMENT: cfg.environment,
            SERVICE_INSTANCE_ID: socket.gethostname(),
            SERVICE_VERSION: os.getenv("QUANTUM_APP_VERSION", "0.0.0"),
        }
    )

    tracer_provider = TracerProvider(
        resource=resource,
        id_generator=RandomIdGenerator(),
        sampler=ParentBased(TraceIdRatioBased(cfg.sample_ratio)),
        span_limits=SpanLimits(
            max_attributes=128,
            max_events=128,
            max_links=32,
        ),
    )

    if cfg.exporter == "console":
        tracer_provider.add_span_processor(
            BatchSpanProcessor(
                ConsoleSpanExporter(),
                max_export_batch_size=256,
                schedule_delay_millis=500,
                max_queue_size=4096,
            )
        )

    active_exporter = None
    if cfg.exporter == "otlp":
        exporter = _build_otlp_exporter()
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
        else:
            # Soft fallback: If OTLP is unavailable (package not installed/endpoint down),
            # Init doesn't fail; no explicit export is required.
            pass

    set_tracer_provider(tracer_provider)

    setattr(tracer_provider, "_active_exporter", active_exporter is not None)

    atexit.register(tracer_provider.shutdown)

    # Expose a reference for controlled shutdown in init_observability
    try:
        import quantum.infrastructure.observability.init_observability as _init_mod

        _init_mod._tracer_provider_ref = cast(object, tracer_provider)
    except Exception:
        pass

    return tracer_provider


def _build_otlp_exporter() -> object | None:
    """
    Builds a best-effort OTLP exporter (HTTP or gRPC).

    Supported variables (all optional):
    - QUANTUM_TRACE_OTLP_PROTOCOL: "http" (default) or "grpc"
    - QUANTUM_TRACE_OTLP_ENDPOINT: e.g., "http://127.0.0.1:4318" (HTTP) or "127.0.0.1:4317" (gRPC)
    - QUANTUM_TRACE_OTLP_HEADERS: "k1=v1,k2=v2"
    - QUANTUM_TRACE_OTLP_TIMEOUT_MS: e.g., "10000"
    - QUANTUM_TRACE_OTLP_COMPRESSION: "gzip" | "none"
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

    # Compression
    comp = os.getenv("QUANTUM_TRACE_OTLP_COMPRESSION", "").strip().lower()
    if comp in {"gzip", "gz"}:
        os.environ["OTEL_EXPORTER_OTLP_TRACES_COMPRESSION"] = "gzip"
        os.environ.setdefault("OTEL_EXPORTER_OTLP_COMPRESSION", "gzip")
    elif comp in {"", "none", "0", "false", "off"}:
        os.environ.pop("OTEL_EXPORTER_OTLP_TRACES_COMPRESSION", None)

    if protocol == "grpc":
        if not _HAS_OTLP_GRPC:
            return None
        insecure = os.getenv("QUANTUM_TRACE_OTLP_INSECURE", "1").strip() == "1"
        return OTLPGRPCExporter(
            endpoint=endpoint,
            headers=headers or None,
            timeout=timeout,
            insecure=insecure,
        )
    # default http/protobuf
    if not _HAS_OTLP_HTTP:
        return None
    return OTLPHTTPExporter(
        endpoint=(
            endpoint + "/v1/traces" if not endpoint.endswith("/v1/traces") else endpoint
        ),
        headers=headers or None,
        timeout=timeout,
    )
