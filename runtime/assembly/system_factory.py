from __future__ import annotations

from dataclasses import dataclass

from runtime.bootstrap.runtime_context import RuntimeContext
from runtime.control_plane.http.server import (
    AdminHttpControlPlaneServer,
    NullAdminControlPlaneServer,
)
from runtime.lifecycle.engine import RuntimeLifecycleEngine

from quantum.application.ports.inbound.application_runtime_port import (
    ApplicationRuntimePort,
)
from quantum.application.ports.outbound.event_bus_port import EventBusPort
from quantum.application.services.application_orchestrator import (
    ApplicationOrchestrator,
)
from quantum.infrastructure.events.bus.asyncio_event_bus_adapter import (
    AsyncioEventBusAdapter,
)


@dataclass(frozen=True)
class AssembledRuntime:
    """
    Aggregates the fully wired runtime engine and its associated runtime context.

    Responsibilities:
        - Hold the immutable runtime context (configuration, identity, observability)
        - Hold the fully constructed runtime engine
        - Act as a clear handoff boundary to the deployment shell (`bin/`)

    This object has no lifecycle responsibility; it is a pure aggregate.
    """

    runtime: RuntimeContext
    engine: RuntimeLifecycleEngine


def assemble_runtime(runtime: RuntimeContext) -> AssembledRuntime:
    """
    Build the fully wired runtime system.

    Responsibilities:
        - Instantiate infrastructure adapters required at runtime
        - Instantiate the application orchestrator
        - Instantiate the secured control_plane HTTP control-plane (or a null implementation)
        - Inject all dependencies into the RuntimeEngine

    Architectural Notes:
        - This function is part of the external composition root.
        - It is allowed to import infrastructure-level adapters.
        - No business logic or domain rules are permitted here.
    """
    core_cfg = runtime.config.core

    # Event Bus
    event_bus: EventBusPort = AsyncioEventBusAdapter()

    # Application Orchestrator
    orchestrator: ApplicationRuntimePort = ApplicationOrchestrator(event_bus=event_bus)

    # Admin HTTP Control-Plane
    if core_cfg.quantum_admin_http_enabled:
        admin_http_server = AdminHttpControlPlaneServer(
            host=core_cfg.quantum_admin_http_host,
            port=core_cfg.quantum_admin_http_port,
            base_path=core_cfg.quantum_admin_http_base_path,
            auth_token=core_cfg.quantum_admin_http_token,
            trusted_proxy_cidrs=core_cfg.quantum_admin_http_trusted_proxies,
            runtime_engine=None,
        )
    else:
        admin_http_server = NullAdminControlPlaneServer()

    # Runtime engine
    engine = RuntimeLifecycleEngine(
        app_service=orchestrator,
        event_bus=event_bus,
        admin_http_server=admin_http_server,
        graceful_shutdown_timeout=core_cfg.quantum_shutdown_timeout,
    )

    if isinstance(admin_http_server, AdminHttpControlPlaneServer):
        admin_http_server.bind_runtime_engine(engine)

    return AssembledRuntime(runtime=runtime, engine=engine)
