from __future__ import annotations

import asyncio
import logging

from typing import Any

from quantum.application.ports.outbound.event_bus_port import EventBusPort
from quantum.application.ports.outbound.observability_port import ObservabilityPort
from quantum.infrastructure.observability.bootstrap.init_manager import (
    init_observability,
)
from quantum.infrastructure.observability.context.run_id import (
    generate_run_id,
    get_run_id,
)
from quantum.infrastructure.observability.tracing.correlation.correlation_id import (
    get_correlation_id,
    new_correlation_id,
)


class ObservabilityDriver(ObservabilityPort):
    """Concrete driver implementing observability access and telemetry control."""

    def __init__(self, event_bus: EventBusPort | None = None) -> None:
        self._logger = logging.getLogger("quantum.observability.driver")
        self._event_bus = event_bus

    def initialize_observability(self) -> None:
        """Initialize the observability stack (logging, metrics, tracing, etc.)."""
        init_observability()
        if self._event_bus:
            try:
                asyncio.run(self._subscribe_to_events())
            except RuntimeError:
                # already inside an event loop (e.g. Streamlit)
                asyncio.get_event_loop().create_task(self._subscribe_to_events())

    async def _subscribe_to_events(self) -> None:
        """Subscribe observability handlers to relevant application events."""
        if not self._event_bus:
            return

        async def on_execution_event(payload: dict[str, Any]) -> None:
            self.emit_event("system.execution_channel", payload)

        async def on_order_submit(payload: dict[str, Any]) -> None:
            self.emit_event("trading.order_submit", payload)

        await self._event_bus.subscribe("system.execution_channel", on_execution_event)
        await self._event_bus.subscribe("trading.order_submit", on_order_submit)

        self._logger.info("[Observability] Subscribed to application event streams.")

    def ensure_run_id(self) -> str:
        """Ensure a unique run_id is available for the current process."""
        rid = get_run_id()
        if not rid:
            rid = generate_run_id()
        return rid

    def ensure_correlation_id(self) -> str:
        """
        Ensure a correlation ID exists for the current async context.
        Generates a new one if missing.
        """
        cid = get_correlation_id()
        if cid is not None:
            return cid

        return new_correlation_id()

    def emit_event(self, topic: str, payload: dict[str, Any]) -> None:
        """Emit an event record to logs and metrics sinks."""
        self._logger.info(
            f"[Observability] Event received: {topic}",
            extra={"attrs": payload},
        )
