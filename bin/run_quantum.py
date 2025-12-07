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

This module SHALL NOT:
- Contain business logic.
- Know about infrastructure adapter types.
- Perform low-level wiring of runtime internals.
"""

from __future__ import annotations

import asyncio
import logging
import signal
import sys

from typing import Final

from runtime.composition.runtime_composer import compose_runtime
from runtime.composition.runtime_system import build_runtime_system

# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Early Stage Minimal Logger                                                 │
# │ Deterministic stderr logging before observability initialized.             │
# ╰────────────────────────────────────────────────────────────────────────────╯
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [Bootstrap] %(levelname)s: %(message)s",
)
LOGGER: Final = logging.getLogger("quantum.bootstrap")


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Entrypoint Logic                                                           │
# ╰────────────────────────────────────────────────────────────────────────────╯
async def main_async() -> int:
    LOGGER.info("Starting Quantum runtime...")

    # 1. Build runtime (config + observability)
    try:
        runtime = compose_runtime()
    except Exception as exc:
        LOGGER.exception("Fatal composition error: %s", exc)
        return 2

    # 2. Initialize observability stack
    if not runtime.initialize_observability():
        LOGGER.error("Observability startup failed")
        try:
            runtime.shutdown_observability()
        except Exception:
            LOGGER.exception("Error while rolling back observability init")
        return 3

    # 3. Build the fully-wired runtime system (engine + internal transports)
    system = build_runtime_system(runtime)
    engine = system.engine

    # 4. Register POSIX signals in the current asyncio loop
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

    # 5. Start the runtime engine (async)
    try:
        await engine.start()
    finally:
        # 6. Shutdown observability
        LOGGER.info("[Runtime] Shutting down observability")
        system.runtime.shutdown_observability()

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
