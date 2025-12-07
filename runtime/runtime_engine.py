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
        LOGGER.debug("[Runtime Engine] Stopping application orchestrator.")
        with self._suppress_cancel():
            await self._app.stop()

        LOGGER.debug("[Runtime Engine] Closing event bus.")
        with self._suppress_cancel():
            await self._event_bus.close()

        LOGGER.debug("[Runtime Engine] Stopping HTTP supervisor server.")
        await self._admin_http_server.stop()

    async def _shutdown(self) -> None:
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
        """Start and run the Quantum Runtime Engine."""

        if self._fsm.state != RuntimeState.STOPPED:
            raise RuntimeInvalidStateError(
                f"RuntimeEngine.start() illegal in state {self._fsm.state.value}"
            )

        self._fsm.transition(RuntimeState.STARTING)
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

            self._fsm.transition(RuntimeState.RUNNING)
            LOGGER.info("[Runtime Engine] Runtime is now operational.")

            try:
                await self._main_loop()
            finally:
                await self._shutdown()

        except Exception:
            LOGGER.exception("[Runtime Engine] Fatal error during startup.")
            self._fsm.transition(RuntimeState.STOPPING)
            await self._shutdown()
            raise

    async def request_shutdown(self) -> None:
        if self._fsm.state not in {RuntimeState.RUNNING, RuntimeState.STARTING}:
            LOGGER.warning(
                "[Runtime Engine] Shutdown request ignored (state: %s).",
                self._fsm.state.value,
            )
            return

        LOGGER.warning("[Runtime Engine] Shutdown requested.")
        self._shutdown_requested.set()
        await self._admin_http_server.stop()
