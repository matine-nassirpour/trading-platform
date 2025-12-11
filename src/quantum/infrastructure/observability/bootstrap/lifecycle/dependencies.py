from __future__ import annotations

from dataclasses import dataclass

from quantum.infrastructure.observability.bootstrap.health_registry import (
    HealthRegistry,
    build_health_registry,
)
from quantum.infrastructure.observability.bootstrap.init_diagnostics import (
    BootstrapDiagnostics,
    build_bootstrap_diagnostics,
)
from quantum.infrastructure.observability.bootstrap.lifecycle.implementations.logging_initializer_impl import (
    LoggingInitializerImpl,
)
from quantum.infrastructure.observability.bootstrap.lifecycle.implementations.metrics_initializer_impl import (
    MetricsInitializerImpl,
)
from quantum.infrastructure.observability.bootstrap.lifecycle.implementations.tracing_initializer_impl import (
    TracingInitializerImpl,
)
from quantum.infrastructure.observability.bootstrap.lifecycle.protocols.logging_initializer import (
    LoggingInitializer,
)
from quantum.infrastructure.observability.bootstrap.lifecycle.protocols.metrics_initializer import (
    MetricsInitializer,
)
from quantum.infrastructure.observability.bootstrap.lifecycle.protocols.tracing_initializer import (
    TracingInitializer,
)


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Dependency Bundle                                                          │
# ╰────────────────────────────────────────────────────────────────────────────╯
@dataclass(frozen=True)
class ObservabilityDependencies:
    """
    Pure Composition Root for Observability.
    """

    logging_initializer: LoggingInitializer
    tracing_initializer: TracingInitializer
    metrics_initializer: MetricsInitializer
    health_registry: HealthRegistry
    diagnostics: BootstrapDiagnostics


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Factory — used by LifecycleService during instantiation                    │
# ╰────────────────────────────────────────────────────────────────────────────╯
def create_observability_dependencies() -> ObservabilityDependencies:
    """
    Composition Root for all Observability dependencies.

    IMPORTANT:
        No external configuration is accessed here.
        No global state is mutated.
        No OpenTelemetry / logging / metrics side effects occur here.

    Pure dependency construction.
    """

    health_registry = build_health_registry(prefix="quantum")
    diagnostics = build_bootstrap_diagnostics(prefix="quantum")

    return ObservabilityDependencies(
        logging_initializer=LoggingInitializerImpl(),
        tracing_initializer=TracingInitializerImpl(),
        metrics_initializer=MetricsInitializerImpl(),
        health_registry=health_registry,
        diagnostics=diagnostics,
    )
