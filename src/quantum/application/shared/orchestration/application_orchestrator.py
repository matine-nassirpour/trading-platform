import asyncio
import logging

from typing import Final

from quantum.application.ports.inbound.messaging.domain_event_subscription_registry import (
    DomainEventSubscriptionRegistry,
)

LOGGER: Final = logging.getLogger("quantum.application.app_service")


class ApplicationOrchestrator:
    """
    Application lifecycle coordinator.

    Responsibilities:
    - register application-level event handlers;
    - expose lifecycle to runtime;
    - supervise application-owned background tasks.

    Non-responsibilities:
    - no business logic;
    - no command execution;
    - no infrastructure I/O directly;
    - no domain mutation.
    """

    __slots__ = ("_subscriptions", "_running", "_tasks")

    def __init__(
        self,
        *,
        subscriptions: DomainEventSubscriptionRegistry,
    ) -> None:
        self._subscriptions = subscriptions
        self._running = False
        self._tasks: list[asyncio.Task[None]] = []

        # Instantiate all underlying application services
        # self._execution = ExecutionService(event_bus=event_bus)

    # --- Lifecycle ------------------------------------------------------------

    async def start(self) -> None:
        """Start the application layer."""
        if self._running:
            return

        LOGGER.info("[App] Starting application layer...")

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

    # --- Handler registration -------------------------------------------------

    async def _register_handlers(self) -> None:
        """
        Register all command and domain-event handlers.

        Initially empty, but this is where your
        event-driven architecture will be wired.
        """
        # Example placeholder:
        # await self._event_bus.subscribe("trade.executed", self.on_trade_executed)

        pass

    # --- Example handler template ---------------------------------------------

    @staticmethod
    async def on_trade_executed(payload: dict) -> None:
        """
        Example handler for illustration.
        """
        LOGGER.info("[App] Received trade.executed event: %s", payload)
