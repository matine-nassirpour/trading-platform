from __future__ import annotations

import asyncio
import logging

from typing import Final

from runtime.control_plane.admin_http.server import RuntimeSupervisorHTTPServer

from quantum.application.ports.outbound.event_bus_port import EventBusPort
from quantum.application.services.application_orchestrator import (
    ApplicationOrchestrator,
)

LOGGER: Final = logging.getLogger("quantum.runtime.engine")


class RuntimeEngine:
    """
    Quantum Runtime Engine (asynchronous)

    Responsibilities
    ----------------
    • Orchestration root for the entire Quantum runtime lifecycle.
    • Drives application-level async behaviors (event-driven loop).
    • Owns the event bus lifecycle (init → run → shutdown).
    • Provides deterministic startup and teardown semantics.
    • Zero domain knowledge, zero infrastructure knowledge.
    • Stable API designed for 10+ years compatibility.

    Architectural Position
    ----------------------
    This class is the OS-internal orchestrator.

    - Does NOT import infrastructure directly (except adapters already
      wired by the runtime composer).
    - Does NOT contain business logic.
    - Does NOT manipulate observability, logging, or configuration.

    All external dependencies are injected (DIP-compliant).
    """

    def __init__(
        self,
        *,
        app_service: ApplicationOrchestrator,
        event_bus: EventBusPort,
        graceful_shutdown_timeout: float = 5.0,
    ) -> None:
        self._app = app_service
        self._event_bus = event_bus
        self._graceful_timeout = graceful_shutdown_timeout

        self._shutdown_requested = asyncio.Event()
        self._runtime_supervisor_http_server = RuntimeSupervisorHTTPServer()

        self._running = False
        self._shutdown_started = False

    # --------------------------------------------------------------------------
    # Public API
    # --------------------------------------------------------------------------
    async def start(self) -> None:
        """
        Start and run the Quantum Runtime Engine.

        Steps:
            1. Initialize event bus.
            2. Start application services.
            3. Enter cooperative async loop.
            4. Wait for shutdown signal.
        """
        if self._running:
            LOGGER.warning("[Runtime] start() called but engine is already running")
            return

        LOGGER.info("[Runtime] Starting Quantum Runtime Engine")

        await self._runtime_supervisor_http_server.start()
        await self._event_bus.initialize()
        await self._app.start()

        self._running = True
        LOGGER.info("[Runtime] Runtime is now operational")

        try:
            await self._main_loop()
        finally:
            await self._shutdown()

    async def request_shutdown(self) -> None:
        """
        External trigger for shutdown.

        Called by:
        - OS signals (SIGINT, SIGTERM)
        - Streamlit UI
        - Application watchdog
        """
        if not self._shutdown_requested.is_set():
            LOGGER.warning("[Runtime] Shutdown requested")
            self._shutdown_requested.set()
            await self._runtime_supervisor_http_server.stop()

    # --------------------------------------------------------------------------
    # Internal Lifecycle
    # --------------------------------------------------------------------------
    async def _main_loop(self) -> None:
        """
        Main cooperative loop of the runtime engine.

        Responsibilities:
        - keep the runtime responsive
        - handle graceful cancellation
        - no business logic runs here
        """
        while not self._shutdown_requested.is_set():
            await asyncio.sleep(0.05)  # Cooperative scheduling

    async def _shutdown(self) -> None:
        """
        Deterministic and safe shutdown sequence.
        """
        if self._shutdown_started:
            LOGGER.warning("[Runtime] Shutdown already in progress — skipping.")
            return

        self._shutdown_started = True
        LOGGER.info("[Runtime] Performing graceful shutdown")

        try:
            await asyncio.wait_for(self._do_shutdown(), timeout=self._graceful_timeout)
        except TimeoutError:
            LOGGER.error("[Runtime] Forced shutdown (timeout exceeded)")

        self._running = False
        LOGGER.info("[Runtime] Shutdown complete")

    async def _do_shutdown(self) -> None:
        """
        Actual shutdown logic.

        Order:
            1. Stop application orchestrator
            2. Close event bus
            3. Release OS-level resources
        """
        LOGGER.debug("[Runtime] Stopping application orchestrator")
        with self._suppress_cancel():
            await self._app.stop()

        LOGGER.debug("[Runtime] Closing event bus")
        with self._suppress_cancel():
            await self._event_bus.close()

    # --------------------------------------------------------------------------
    # Utilities
    # --------------------------------------------------------------------------
    class _suppress_cancel:
        """
        Suppress CancelledError inside a context.

        Ensures deterministic shutdown even if tasks were cancelled.
        """

        def __enter__(self) -> None:
            return None

        def __exit__(self, exc_type, exc, tb) -> bool:
            # Convert CancelledError to “handled”
            return exc_type is asyncio.CancelledError
