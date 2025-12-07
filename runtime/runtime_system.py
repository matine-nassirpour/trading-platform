from __future__ import annotations

from dataclasses import dataclass

from runtime.control_plane.admin_http.server import (
    NullRuntimeSupervisorHTTPServer,
    RuntimeSupervisorHTTPServer,
)
from runtime.runtime_composer import QuantumRuntime
from runtime.runtime_engine import RuntimeEngine

from quantum.application.ports.outbound.event_bus_port import EventBusPort
from quantum.application.services.application_orchestrator import (
    ApplicationOrchestrator,
)
from quantum.infrastructure.eventbus.asyncio_event_bus_adapter import (
    AsyncioEventBusAdapter,
)


@dataclass(frozen=True)
class RuntimeSystem:
    """
    Aggregates the fully wired runtime engine and its associated runtime context.

    This type is intentionally small and explicit:
    - `runtime` → configuration, identity, observability lifecycle
    - `engine`  → async orchestration of the running system
    """

    runtime: QuantumRuntime
    engine: RuntimeEngine


def build_runtime_system(runtime: QuantumRuntime) -> RuntimeSystem:
    """
    Build the fully wired runtime system (engine + internal transports).

    Responsibilities:
    - Instantiate the event bus adapter.
    - Instantiate the application orchestrator.
    - Instantiate the admin HTTP supervisor server, configured from CoreSettings.
    - Instantiate the RuntimeEngine with all dependencies injected.

    This function lives in the `runtime/` layer, i.e. outside the Clean Architecture
    core, and is therefore allowed to import infrastructure-level adapters.
    """
    core_cfg = runtime.core_settings

    # Event bus
    event_bus: EventBusPort = AsyncioEventBusAdapter()

    # Application orchestrator
    orchestrator = ApplicationOrchestrator(event_bus=event_bus)

    # Admin HTTP supervisor (control-plane entrypoint)
    if core_cfg.quantum_admin_http_enabled:
        admin_http_server = RuntimeSupervisorHTTPServer(
            host=core_cfg.quantum_admin_http_host,
            port=core_cfg.quantum_admin_http_port,
            base_path=core_cfg.quantum_admin_http_base_path,
        )
    else:
        admin_http_server = NullRuntimeSupervisorHTTPServer()

    # Runtime engine
    engine = RuntimeEngine(
        app_service=orchestrator,
        event_bus=event_bus,
        admin_http_server=admin_http_server,
    )

    return RuntimeSystem(runtime=runtime, engine=engine)
