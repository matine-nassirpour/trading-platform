from __future__ import annotations

from dataclasses import dataclass

from runtime.composition.composer import QuantumRuntime
from runtime.control_plane.admin_http.server import (
    NullRuntimeSupervisorHTTPServer,
    RuntimeSupervisorHTTPServer,
)
from runtime.kernel.engine import RuntimeEngine

from quantum.application.ports.inbound.application_runtime_port import (
    ApplicationRuntimePort,
)
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

    Responsibilities:
        - Hold the immutable runtime context (configuration, identity, observability)
        - Hold the fully constructed runtime engine
        - Act as a clear handoff boundary to the deployment shell (`bin/`)
    """

    runtime: QuantumRuntime
    engine: RuntimeEngine


def build_runtime_system(runtime: QuantumRuntime) -> RuntimeSystem:
    """
    Build the fully wired runtime system.

    Responsibilities:
        - Instantiate infrastructure adapters required at runtime
        - Instantiate the application orchestrator
        - Instantiate the secured admin HTTP control-plane (or a null implementation)
        - Inject all dependencies into the RuntimeEngine

    Architectural Notes:
        - This function is part of the external composition root.
        - It is allowed to import infrastructure-level adapters.
        - No business logic or domain rules are permitted here.
    """
    core_cfg = runtime.core_settings

    # Event Bus
    event_bus: EventBusPort = AsyncioEventBusAdapter()

    # Application Orchestrator
    orchestrator: ApplicationRuntimePort = ApplicationOrchestrator(event_bus=event_bus)

    # Admin HTTP Control-Plane
    if core_cfg.quantum_admin_http_enabled:
        admin_http_server = RuntimeSupervisorHTTPServer(
            host=core_cfg.quantum_admin_http_host,
            port=core_cfg.quantum_admin_http_port,
            base_path=core_cfg.quantum_admin_http_base_path,
            auth_token=core_cfg.quantum_admin_http_token,
            trust_proxy_headers=core_cfg.quantum_admin_http_trust_proxy,
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
