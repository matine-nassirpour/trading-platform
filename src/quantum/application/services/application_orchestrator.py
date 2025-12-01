from __future__ import annotations

import asyncio
import logging

from typing import Final

from quantum.application.ports.outbound.event_bus_port import EventBusPort

LOGGER: Final = logging.getLogger("quantum.application.app_service")


class ApplicationOrchestrator:
    """
    Root of the Application Layer.

    Responsibilities
    ----------------
    • Register command/event handlers
    • Connect domain workflows to the event bus
    • Expose async start()/stop() lifecycle to the runtime
    • Coordinate application-level operations
    • Contain zero business logic (delegates to domain services/use cases)

    Notes
    -----
    This class is intentionally thin at the beginning.
    Its main function is to structure the future application workflows.
    """

    def __init__(self, *, event_bus: EventBusPort) -> None:
        self._event_bus = event_bus

        self._running = False
        self._tasks: list[asyncio.Task] = []

        # Instantiate all underlying application services
        # self._execution = ExecutionService(event_bus=event_bus)

    # --------------------------------------------------------------------------
    # Lifecycle
    # --------------------------------------------------------------------------
    async def start(self) -> None:
        """Start the application layer."""
        if self._running:
            return

        LOGGER.info("[App] Starting application layer…")

        # Register event handlers
        await self._register_handlers()

        # await self._execution.start()

        self._running = True
        LOGGER.info("[App] Application layer started.")

    async def stop(self) -> None:
        """Graceful shutdown."""
        if not self._running:
            return

        LOGGER.info("[App] Stopping application layer…")

        # await self._execution.stop()
        self._running = False

        for task in self._tasks:
            task.cancel()

        LOGGER.info("[App] Application layer stopped.")

    # --------------------------------------------------------------------------
    # Handler registration
    # --------------------------------------------------------------------------
    async def _register_handlers(self) -> None:
        """
        Register all command and domain-event handlers.

        Initially empty, but this is where your
        event-driven architecture will be wired.
        """
        # Example placeholder:
        # await self._event_bus.subscribe("trade.executed", self.on_trade_executed)

        pass

    # --------------------------------------------------------------------------
    # Example handler template
    # --------------------------------------------------------------------------
    @staticmethod
    async def on_trade_executed(payload: dict) -> None:
        """
        Example handler for illustration.
        """
        LOGGER.info("[App] Received trade.executed event: %s", payload)
