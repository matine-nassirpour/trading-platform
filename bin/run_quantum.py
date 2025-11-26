"""
Quantum Runtime Entrypoint

Responsibilities
----------------
    • Bootstrapping the runtime via runtime_composer
    • Performing safe early-stage logging initialization
    • Handling OS signals (SIGINT, SIGTERM) for graceful shutdown
    • Exposing deterministic exit codes for orchestration systems
    • Ensuring observability and configuration initialization succeed
    • Protecting against partial initialization or inconsistent state

This script acts as the “Deployment Shell” in Clean Architecture terminology.
It intentionally remains thin and free of domain/application logic.
"""

from __future__ import annotations

import asyncio
import logging
import signal
import sys
import threading

from typing import Final

from runtime.runtime_composer import compose_runtime
from runtime.runtime_engine import RuntimeEngine

from quantum.application.ports.outbound.event_bus_port import EventBusPort
from quantum.application.services.application_orchestrator import (
    ApplicationOrchestrator,
)
from quantum.infrastructure.eventbus.asyncio_event_bus_adapter import (
    AsyncioEventBusAdapter,
)

# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Logging — Early Stage Minimal Logger                                       │
# │ Before observability initialization, we want deterministic stderr logging. │
# ╰────────────────────────────────────────────────────────────────────────────╯
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [bootstrap] %(levelname)s: %(message)s",
)
LOGGER: Final = logging.getLogger("quantum.bootstrap")


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Signal Handling                                                            │
# ╰────────────────────────────────────────────────────────────────────────────╯
_shutdown_event = threading.Event()


def _handle_signal(signum: int, frame) -> None:
    """Handle termination signals from OS."""
    LOGGER.warning("Received signal %s — initiating shutdown...", signum)
    _shutdown_event.set()


def _register_signals() -> None:
    """Register POSIX signal handlers."""
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, _handle_signal)
    LOGGER.info("Signal handlers registered.")


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Entrypoint Logic                                                           │
# ╰────────────────────────────────────────────────────────────────────────────╯
def main() -> int:
    LOGGER.info("Starting Quantum runtime…")

    _register_signals()

    # 1) Build base runtime (config + observability)
    try:
        runtime = compose_runtime()
    except Exception as exc:
        LOGGER.exception("Fatal composition error: %s", exc)
        return 2

    # 2) Initialize observability
    if not runtime.initialize_observability():
        LOGGER.error("Observability startup failed")
        return 3

    # 3) Build application shell (event bus + orchestrator + engine)
    event_bus: EventBusPort = AsyncioEventBusAdapter()
    orchestrator = ApplicationOrchestrator(event_bus=event_bus)
    engine = RuntimeEngine(app_service=orchestrator, event_bus=event_bus)

    # 4) Run async engine
    async def _run():
        await engine.start()

    asyncio.run(_run())

    # 5) Wait for signal
    _shutdown_event.wait()

    # 6) Engine shutdown
    asyncio.run(engine.request_shutdown())

    # 7) Observability shutdown
    runtime.shutdown_observability()

    LOGGER.info("Quantum runtime exited cleanly.")
    return 0


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ CLI Entrypoint                                                             │
# ╰────────────────────────────────────────────────────────────────────────────╯
if __name__ == "__main__":
    sys.exit(main())
