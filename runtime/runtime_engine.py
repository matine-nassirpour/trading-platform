from __future__ import annotations

import asyncio
import logging

from typing import Final, Protocol

from quantum.application.ports.outbound.event_bus_port import EventBusPort
from quantum.application.services.application_orchestrator import (
    ApplicationOrchestrator,
)

LOGGER: Final = logging.getLogger("quantum.runtime.engine")


class AdminHTTPServerPort(Protocol):
    """
    Minimal administrative HTTP server port.
    This is an OS-/transport-level concern.
    """

    async def start(self) -> None: ...

    async def stop(self) -> None: ...


class RuntimeEngine:
    """
    Quantum Runtime Engine (asynchronous)

    Responsibilities:
    • Orchestration root for the entire Quantum runtime lifecycle.
    • Drives application-level async behaviors (event-driven loop).
    • Owns the event bus lifecycle (init → run → shutdown).
    • Owns the admin HTTP supervisor lifecycle (start → run → stop),
      via an abstract port (AdminHTTPServerPort).
    • Provides deterministic startup and teardown semantics.
    • Zero domain knowledge, zero infrastructure knowledge.
    • Stable API designed for 10+ years compatibility.

    Architectural Position:
    This class is the OS-internal orchestrator.
    - Does NOT import infrastructure directly.
    - Does NOT contain business logic.
    - Does NOT manipulate observability, logging, or configuration.
    - All external dependencies are injected (DIP-compliant).
    """

    def __init__(
        self,
        *,
        app_service: ApplicationOrchestrator,
        event_bus: EventBusPort,
        admin_http_server: AdminHTTPServerPort,
        graceful_shutdown_timeout: float = 5.0,
    ) -> None:
        self._app = app_service
        self._event_bus = event_bus
        self._admin_http_server = admin_http_server
        self._graceful_timeout = graceful_shutdown_timeout

        self._shutdown_requested = asyncio.Event()

        self._running = False
        self._shutdown_started = False

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

    async def _do_shutdown(self) -> None:
        LOGGER.debug("[Runtime Engine] Stopping application orchestrator.")
        with self._suppress_cancel():
            await self._app.stop()

        LOGGER.debug("[Runtime Engine] Closing event bus.")
        with self._suppress_cancel():
            await self._event_bus.close()

        LOGGER.debug("[Runtime Engine] Stopping HTTP supervisor server.")
        await self._admin_http_server.stop()

    async def _shutdown(self) -> None:
        """
        Deterministic and safe shutdown sequence.
        """
        if self._shutdown_started:
            LOGGER.warning("[Runtime Engine] Shutdown already in progress — skipping.")
            return

        self._shutdown_started = True
        LOGGER.info("[Runtime Engine] Performing graceful shutdown.")

        try:
            await asyncio.wait_for(self._do_shutdown(), timeout=self._graceful_timeout)
        except TimeoutError:
            LOGGER.error("[Runtime Engine] Forced shutdown (timeout exceeded).")

        self._running = False
        LOGGER.info("[Runtime Engine] Shutdown complete.")

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

    # --------------------------------------------------------------------------
    # Public API
    # --------------------------------------------------------------------------
    async def start(self) -> None:
        """Start and run the Quantum Runtime Engine."""

        if self._running:
            return

        LOGGER.info("[Runtime Engine] Starting Quantum Runtime Engine.")

        try:
            await self._admin_http_server.start()
            try:
                await self._event_bus.initialize()
                try:
                    await self._app.start()
                except Exception:
                    # rollback event bus
                    with self._suppress_cancel():
                        await self._event_bus.close()
                    raise
            except Exception:
                # rollback HTTP server
                await self._admin_http_server.stop()
                raise

            self._running = True
            LOGGER.info("[Runtime Engine] Runtime is now operational.")

            try:
                await self._main_loop()
            finally:
                await self._shutdown()

        except Exception:
            LOGGER.exception("[Runtime Engine] Fatal error during startup.")
            raise

    async def request_shutdown(self) -> None:
        """
        External trigger for shutdown.

        Called by:
        - OS signals (SIGINT, SIGTERM)
        - Streamlit UI
        - Application watchdog
        """
        if not self._shutdown_requested.is_set():
            LOGGER.warning("[Runtime Engine] Shutdown requested.")
            self._shutdown_requested.set()
            await self._admin_http_server.stop()
