from dataclasses import dataclass
from threading import Lock

from quantum.infrastructure.observability.bootstrap.health_registry import (
    HealthRegistry,
)
from quantum.infrastructure.observability.bootstrap.init_diagnostics import (
    BootstrapDiagnostics,
)
from quantum.infrastructure.observability.bootstrap.lifecycle.dependencies import (
    ObservabilityDependencies,
)
from quantum.infrastructure.observability.bootstrap.lifecycle.lifecycle import (
    LifecycleService,
)


@dataclass(frozen=True)
class ObservabilityRuntimeContext:
    """
    Immutable runtime context for the Observability subsystem.

    Contains:
        • health: HealthRegistry
        • diagnostics: BootstrapDiagnostics
        • lifecycle: LifecycleService (the orchestrator)

    All internal state mutations occur ONLY inside LifecycleService.
    This object itself is immutable and safe for concurrent readers.
    """

    health: HealthRegistry
    diagnostics: BootstrapDiagnostics
    lifecycle: LifecycleService


class _RuntimeContextHolder:
    """
    Thread-safe singleton holder for ObservabilityRuntimeContext.

    - install() may be called exactly once per process.
    - get() returns the immutable context or raises if uninitialized.

    This class is intentionally internal:
        It is NOT a service locator.
        It is simply a controlled, explicit runtime mount-point.
    """

    _lock = Lock()
    _context: ObservabilityRuntimeContext | None = None

    @classmethod
    def install(cls, *, deps: ObservabilityDependencies) -> None:
        """
        Install the runtime context exactly once.
        Safe to call multiple times; subsequent calls are ignored.

        NEVER replaced at runtime → deterministic & certifiable.
        """
        with cls._lock:
            if cls._context is not None:
                return

            ctx = ObservabilityRuntimeContext(
                health=deps.health_registry,
                diagnostics=deps.diagnostics,
                lifecycle=LifecycleService(deps),
            )
            cls._context = ctx

    @classmethod
    def get(cls) -> ObservabilityRuntimeContext:
        """
        Access the immutable runtime context.

        Raises:
            RuntimeError if the context is not installed.
        """
        if cls._context is None:
            raise RuntimeError(
                "ObservabilityRuntimeContext accessed before initialization."
            )
        return cls._context
