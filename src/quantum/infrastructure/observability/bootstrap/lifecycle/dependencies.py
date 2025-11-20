from __future__ import annotations

from dataclasses import dataclass

from quantum.infrastructure.observability.bootstrap.health_registry import (
    HealthRegistry,
)
from quantum.infrastructure.observability.bootstrap.init_diagnostics import (
    BootstrapDiagnostics,
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
from quantum.infrastructure.observability.bootstrap.lifecycle.protocols.build_info_provider import (
    BuildInfoProvider,
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
from quantum.infrastructure.observability.metrics.collectors.health_collector import (
    refresh_build_info_from_env,
)


class _BuildInfoProviderImpl(BuildInfoProvider):
    """Simple adapter around the env-based build info refresher."""

    def refresh(self) -> None:
        refresh_build_info_from_env()


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Dependency Bundle                                                          │
# ╰────────────────────────────────────────────────────────────────────────────╯
@dataclass(frozen=True)
class ObservabilityDependencies:
    """
    Immutable composition bundle for all observability services.

    This is the *only* place where implementations are selected.
    No other module decides which concrete classes to use.

    This dramatically increases modularity, testability, and long-term
    maintainability (10+ years).
    """

    logging_initializer: LoggingInitializer
    tracing_initializer: TracingInitializer
    metrics_initializer: MetricsInitializer
    health_registry: HealthRegistry
    diagnostics: BootstrapDiagnostics
    build_info_provider: BuildInfoProvider


# ---------------------------------------------------------------------------
# Factory — used by LifecycleService during instantiation
# ---------------------------------------------------------------------------
def create_observability_dependencies() -> ObservabilityDependencies:
    """
    Composition Root for all Observability dependencies.

    IMPORTANT:
        No external configuration is accessed here.
        No global state is mutated.
        No OpenTelemetry / logging / metrics side effects occur here.

    Pure dependency construction.
    """

    return ObservabilityDependencies(
        logging_initializer=LoggingInitializerImpl(),
        tracing_initializer=TracingInitializerImpl(),
        metrics_initializer=MetricsInitializerImpl(),
        health_registry=HealthRegistry.get_instance(),
        diagnostics=BootstrapDiagnostics.get_instance(),
        build_info_provider=_BuildInfoProviderImpl(),
    )
