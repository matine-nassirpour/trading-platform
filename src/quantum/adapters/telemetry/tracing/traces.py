import atexit
import socket
from typing import Literal

from opentelemetry.sdk.resources import (
    DEPLOYMENT_ENVIRONMENT,
    SERVICE_INSTANCE_ID,
    SERVICE_NAME,
    SERVICE_NAMESPACE,
    Resource,
)
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.trace.id_generator import RandomIdGenerator
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased
from opentelemetry.trace import TracerProvider as TracerProviderInterface
from opentelemetry.trace import set_tracer_provider


class TracingConfig:
    def __init__(
        self,
        service_name: str,
        environment: str,
        namespace: str,
        exporter: Literal["console", "none"] = "console",
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
        }
    )

    tracer_provider = TracerProvider(
        resource=resource,
        id_generator=RandomIdGenerator(),
        sampler=ParentBased(TraceIdRatioBased(cfg.sample_ratio)),
    )

    if cfg.exporter == "console":
        tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    set_tracer_provider(tracer_provider)

    atexit.register(tracer_provider.shutdown)
    return tracer_provider
