"""
Quantum Runtime Entrypoint (Async + Signals)

Responsibilities
----------------
- Fully async bootstrap.
- Proper POSIX signal integration using asyncio loop.
- Deterministic startup and teardown.
- Observability lifecycle supervision.
- No blocking waits / no threading.Event.
- Clean Architecture compliant (deployment shell only).
"""

from __future__ import annotations

import asyncio
import logging
import signal
import sys

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
# │ Early Stage Minimal Logger                                                 │
# │ Deterministic stderr logging before observability initialized.             │
# ╰────────────────────────────────────────────────────────────────────────────╯
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [bootstrap] %(levelname)s: %(message)s",
)
LOGGER: Final = logging.getLogger("quantum.bootstrap")


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Entrypoint Logic                                                           │
# ╰────────────────────────────────────────────────────────────────────────────╯
async def main_async() -> int:
    LOGGER.info("Starting Quantum runtime…")

    # 1. Build runtime (config + observability)
    try:
        runtime = compose_runtime()
    except Exception as exc:
        LOGGER.exception("Fatal composition error: %s", exc)
        return 2

    if not runtime.initialize_observability():
        LOGGER.error("Observability startup failed")
        try:
            runtime.shutdown_observability()
        except Exception:
            LOGGER.exception("Error while rolling back observability init")
        return 3

    # 2. Build application shell (event bus + orchestrator + engine)
    event_bus: EventBusPort = AsyncioEventBusAdapter()
    orchestrator = ApplicationOrchestrator(event_bus=event_bus)
    engine = RuntimeEngine(app_service=orchestrator, event_bus=event_bus)

    # 3) Register POSIX signals in the current asyncio loop
    loop = asyncio.get_running_loop()

    def _handle_sigterm() -> None:
        LOGGER.warning("[Runtime] SIGTERM received — requesting shutdown")
        asyncio.create_task(engine.request_shutdown())

    def _handle_sigint() -> None:
        LOGGER.warning("[Runtime] SIGINT received — requesting shutdown")
        asyncio.create_task(engine.request_shutdown())

    try:
        loop.add_signal_handler(signal.SIGTERM, _handle_sigterm)
        loop.add_signal_handler(signal.SIGINT, _handle_sigint)
    except NotImplementedError:
        # Windows fallback
        LOGGER.warning("Signal handlers not available on this platform.")

    # 4. Start the runtime engine (async)
    try:
        await engine.start()
    finally:
        # 5. Shutdown observability
        LOGGER.info("[Runtime] Shutting down observability")
        runtime.shutdown_observability()

    LOGGER.info("Quantum runtime exited cleanly.")
    return 0


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Synchronous wrapper                                                        │
# ╰────────────────────────────────────────────────────────────────────────────╯
def main() -> int:
    try:
        return asyncio.run(main_async())
    except KeyboardInterrupt:
        LOGGER.warning("Interrupted by user.")
        return 130
    except Exception as exc:
        LOGGER.exception("Unexpected fatal error: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
