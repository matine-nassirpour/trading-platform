from quantum.infrastructure.observability.bootstrap.health_registry import (
    HealthRegistry,
)
from quantum.infrastructure.observability.bootstrap.init_diagnostics import (
    BootstrapDiagnostics,
)


class ObservabilityRuntimeStatusProvider:
    """
    Infrastructure-level accessor for observability internal state.
    """

    _health_registry: HealthRegistry | None = None
    _bootstrap_diagnostics: BootstrapDiagnostics | None = None

    @staticmethod
    def install(health: HealthRegistry, diagnostics: BootstrapDiagnostics) -> None:
        ObservabilityRuntimeStatusProvider._health_registry = health
        ObservabilityRuntimeStatusProvider._bootstrap_diagnostics = diagnostics

    @staticmethod
    def get_health_registry() -> HealthRegistry | None:
        return ObservabilityRuntimeStatusProvider._health_registry

    @staticmethod
    def get_bootstrap_diagnostics() -> BootstrapDiagnostics | None:
        return ObservabilityRuntimeStatusProvider._bootstrap_diagnostics
