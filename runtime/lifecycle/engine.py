from __future__ import annotations

import asyncio
import logging

from typing import Final, Protocol

from runtime.lifecycle.state_machine import (
    RuntimeLifecycleStateMachine,
    RuntimeLifecycleViolation,
    RuntimeState,
)

from quantum.application.ports.inbound.application_runtime_port import (
    ApplicationRuntimePort,
)
from quantum.application.ports.outbound.messaging.domain_event_bus import DomainEventBus

LOGGER: Final = logging.getLogger("quantum.runtime.engine")


class AdminControlPlanePort(Protocol):
    """
    Minimal administrative HTTP server port.
    This is an OS-/transport-level concern.
    """

    async def start(self) -> None: ...

    async def stop(self) -> None: ...


class RuntimeLifecycleEngine:
    """
    Deterministic runtime lifecycle controller.

    Responsibilities:
    • Deterministic orchestration of the runtime lifecycle.
    • Strict lifecycle FSM (STOPPED → STARTING → RUNNING → STOPPING → STOPPED).
    • Drives event bus + application orchestrator + control_plane HTTP supervisor.
    • Zero domain knowledge; fully DIP-compliant.

    Contains:
    - NO business logic
    - NO configuration logic
    - NO transport-specific knowledge
    """

    def __init__(
        self,
        *,
        app_service: ApplicationRuntimePort,
        event_bus: DomainEventBus,
        admin_http_server: AdminControlPlanePort,
        graceful_shutdown_timeout: float = 5.0,
    ) -> None:
        self._app = app_service
        self._event_bus = event_bus
        self._admin_http_server = admin_http_server
        self._graceful_timeout = graceful_shutdown_timeout

        self._shutdown_requested = asyncio.Event()
        self._fsm = RuntimeLifecycleStateMachine()

        # Track partial startup success
        self._http_started = False
        self._bus_initialized = False
        self._app_started = False

        self._shutdown_lock = asyncio.Lock()

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
        Block until a shutdown is requested.
        No busy looping.
        """
        await self._shutdown_requested.wait()

    async def _do_shutdown(self) -> None:
        """
        Deterministic, idempotent shutdown.
        Each subsystem is only shut down if it was successfully started.
        """
        LOGGER.info("[Runtime Engine] Executing orderly shutdown sequence.")

        # APP orchestrator
        if self._app_started:
            LOGGER.debug("[Runtime Engine] Stopping application orchestrator.")
            with self._suppress_cancel():
                await self._app.stop()

        # EVENT BUS
        if self._bus_initialized:
            LOGGER.debug("[Runtime Engine] Closing event bus.")
            with self._suppress_cancel():
                await self._event_bus.close()

        # HTTP SERVER
        if self._http_started:
            LOGGER.debug("[Runtime Engine] Stopping control_plane HTTP server.")
            with self._suppress_cancel():
                await self._admin_http_server.stop()

    async def _shutdown(self) -> None:
        """
        FSM-consistent shutdown entrypoint.
        Ensures a single STOPPING transition.
        """
        async with self._shutdown_lock:
            current = self._fsm.state

            if current == RuntimeState.STOPPED:
                LOGGER.debug("[Runtime Engine] Shutdown requested but already stopped.")
                return

            if current in {RuntimeState.STARTING, RuntimeState.RUNNING}:
                try:
                    self._fsm.transition(RuntimeState.STOPPING)
                except RuntimeLifecycleViolation as exc:
                    LOGGER.error("FSM violation during shutdown: %s", exc)

            LOGGER.info("[Runtime Engine] Graceful shutdown starting.")

            try:
                await asyncio.wait_for(
                    self._do_shutdown(),
                    timeout=self._graceful_timeout,
                )
            except TimeoutError:
                # Raised by asyncio.wait_for() on graceful shutdown timeout
                LOGGER.error(
                    "[Runtime Engine] Forced shutdown: timeout exceeded (%.2fs).",
                    self._graceful_timeout,
                )
            finally:
                # Absolute convergence guarantee
                self._fsm.force_stop()
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
            return exc_type is asyncio.CancelledError

    # --------------------------------------------------------------------------
    # Public API
    # --------------------------------------------------------------------------
    async def start(self) -> None:
        if self._fsm.state != RuntimeState.STOPPED:
            raise RuntimeLifecycleViolation(
                f"RuntimeEngine.start() illegal in state {self._fsm.state.value}"
            )

        # STARTING
        self._fsm.transition(RuntimeState.STARTING)
        LOGGER.info("[Runtime Engine] Starting Quantum Runtime Engine.")

        try:
            # 1. Start control_plane HTTP server
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
        if self._fsm.state not in {
            RuntimeState.STARTING,
            RuntimeState.RUNNING,
            RuntimeState.STOPPING,
        }:
            LOGGER.debug(
                "[Runtime Engine] Shutdown request ignored (state=%s).",
                self._fsm.state.value,
            )
            return

        LOGGER.warning("[Runtime Engine] Shutdown requested.")
        self._shutdown_requested.set()
