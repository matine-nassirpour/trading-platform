from __future__ import annotations

import asyncio
import logging

from typing import Final, Protocol

from runtime.runtime_state import (
    RuntimeInvalidStateError,
    RuntimeState,
    RuntimeStateMachine,
)

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
    • Deterministic orchestration of the runtime lifecycle.
    • Strict lifecycle FSM (STOPPED → STARTING → RUNNING → STOPPING → STOPPED).
    • Drives event bus + application orchestrator + admin HTTP supervisor.
    • Zero domain knowledge; fully DIP-compliant.
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
        self._fsm = RuntimeStateMachine()

        # Track partial startup success
        self._http_started = False
        self._bus_initialized = False
        self._app_started = False

    # --------------------------------------------------------------------------
    # Public API
    # --------------------------------------------------------------------------
    @property
    def state(self) -> RuntimeState:
        return self._fsm.state

    # --------------------------------------------------------------------------
    # Internal Lifecycle
    # --------------------------------------------------------------------------
    async def _main_loop(self) -> None:
        """
        Main cooperative loop of the runtime engine.

        Responsibilities:
        - keep the runtime responsive
        - handle graceful cancellation
        """
        while not self._shutdown_requested.is_set():
            await asyncio.sleep(0.05)  # Cooperative scheduling

    async def _do_shutdown(self) -> None:
        """
        Deterministic, idempotent shutdown.
        Each subsystem is only shut down if it was successfully started.
        """
        LOGGER.info("[Runtime Engine] Executing orderly shutdown sequence.")

        # APP orchestrator
        if self._app_started:
            LOGGER.debug("[Runtime Engine] Stopping app orchestrator.")
            with self._suppress_cancel():
                await self._app.stop()

        # EVENT BUS
        if self._bus_initialized:
            LOGGER.debug("[Runtime Engine] Closing event bus.")
            with self._suppress_cancel():
                await self._event_bus.close()

        # HTTP SERVER
        if self._http_started:
            LOGGER.debug("[Runtime Engine] Stopping admin HTTP server")
            with self._suppress_cancel():
                await self._admin_http_server.stop()

    async def _shutdown(self) -> None:
        """
        FSM-consistent shutdown entrypoint.
        Ensures a single STOPPING transition.
        """
        # Transition only if needed
        if self._fsm.state != RuntimeState.STOPPING:
            try:
                self._fsm.transition(RuntimeState.STOPPING)
            except RuntimeInvalidStateError as exc:
                LOGGER.error("Illegal shutdown transition: %s", exc)

        LOGGER.info("[Runtime Engine] Graceful shutdown starting.")

        try:
            await asyncio.wait_for(self._do_shutdown(), timeout=self._graceful_timeout)
        except TimeoutError:
            LOGGER.error("[Runtime Engine] Forced shutdown (timeout exceeded).")

        self._fsm.transition(RuntimeState.STOPPED)
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
        """
        Deterministic startup pipeline with rollback.
        """

        if self._fsm.state != RuntimeState.STOPPED:
            raise RuntimeInvalidStateError(
                f"RuntimeEngine.start() illegal in state {self._fsm.state.value}"
            )

        # STARTING
        self._fsm.transition(RuntimeState.STARTING)
        LOGGER.info("[Runtime Engine] Starting Quantum Runtime Engine.")

        try:
            # 1. Start admin HTTP server
            await self._admin_http_server.start()
            self._http_started = True

            # 2. Initialize event bus
            await self._event_bus.initialize()
            self._bus_initialized = True

            # 3. Start application orchestrator
            await self._app.start()
            self._app_started = True

            # RUNNING
            self._fsm.transition(RuntimeState.RUNNING)
            LOGGER.info("[Runtime Engine] Runtime is now operational.")

            try:
                await self._main_loop()
            finally:
                await self._shutdown()

        except Exception:
            LOGGER.exception("[Runtime Engine] Fatal error during startup.")
            await self._shutdown()
            raise

    async def request_shutdown(self) -> None:
        """
        Asynchronous external shutdown request.
        Idempotent.
        """
        if self._fsm.state not in {RuntimeState.STARTING, RuntimeState.RUNNING}:
            LOGGER.warning(
                "[Runtime Engine] Shutdown request ignored (state: %s).",
                self._fsm.state.value,
            )
            return

        LOGGER.warning("[Runtime Engine] Shutdown requested")
        self._shutdown_requested.set()
