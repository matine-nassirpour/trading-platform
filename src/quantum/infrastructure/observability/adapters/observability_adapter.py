from __future__ import annotations

import asyncio
import logging

from collections.abc import Iterator, Mapping
from typing import Any

from prometheus_client import REGISTRY, Metric

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


class ObservabilityAdapter(ObservabilityPort):
    """Concrete adapter implementing observability access and telemetry control."""

    def __init__(self, event_bus: EventBusPort | None = None) -> None:
        self._logger = logging.getLogger("quantum.observability.adapter")
        self._event_bus = event_bus

    # --------------------------------------------------------------------------
    # Lifecycle
    # --------------------------------------------------------------------------
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

    # --------------------------------------------------------------------------
    # IDs and metrics access
    # --------------------------------------------------------------------------
    def ensure_run_id(self) -> str:
        """Ensure a unique run_id is available for the current process."""
        rid = get_run_id()
        if not rid:
            rid = generate_run_id()
        return rid

    def get_correlation_id(self) -> str | None:
        """
        Return the current correlation ID from context (if any).
        """
        return get_correlation_id()

    def ensure_correlation_id(self) -> str:
        """
        Ensure a correlation ID exists for the current async context.
        Generates a new one if missing.
        """
        cid = get_correlation_id()
        if cid is not None:
            return cid

        return new_correlation_id()

    def collect_metrics(self) -> list[Mapping[str, Any]]:
        """Return all currently registered metrics (as collected samples)."""
        try:
            metrics = list(REGISTRY.collect())
            self._logger.debug("Collected %d metrics from REGISTRY.", len(metrics))
            return [m.__dict__ for m in metrics]
        except Exception as exc:
            self._logger.warning("Metrics collection failed: %s", exc)
            return []

    def get_gauge_value(self, name: str) -> float | None:
        """Return the value of a gauge metric without labels."""
        try:
            for metric in REGISTRY.collect():
                for s in getattr(metric, "samples", ()):
                    if s.name == name and not s.labels:
                        return float(s.value)
            return None
        except Exception as exc:
            self._logger.debug("gauge_value(%s) failed: %s", name, exc)
            return None

    def get_counter_value(self, name: str) -> float | None:
        """Alias to get_gauge_value (for counter metrics)."""
        return self.get_gauge_value(name)

    def get_histogram_quantiles(
        self,
        metric_name: str,
        quantiles: tuple[float, ...] = (0.5, 0.95, 0.99),
    ) -> dict[str, float | None]:
        """Approximate quantiles from histogram buckets."""
        try:
            buckets, total_count = self._accumulate_histogram_buckets(metric_name)
            sorted_bounds = sorted(buckets.items(), key=lambda kv: kv[0])
            total = total_count or (sorted_bounds[-1][1] if sorted_bounds else 0.0)
            return self._compute_quantiles(sorted_bounds, quantiles, total)
        except Exception as exc:
            self._logger.debug("Failed to compute histogram quantiles: %s", exc)
            return {f"p{int(q * 100)}": None for q in quantiles}

    # --------------------------------------------------------------------------
    # Internal Helpers
    # --------------------------------------------------------------------------
    def _accumulate_histogram_buckets(
        self, metric_name: str
    ) -> tuple[dict[float, float], float]:
        """
        Collect and aggregate bucket counts and totals for a given histogram metric.
        Returns (buckets, total_count).
        """
        buckets: dict[float, float] = {}
        total_count = 0.0

        for metric in self._collect_histogram_samples(metric_name):
            for s in getattr(metric, "samples", ()):
                n = s.name
                if n.endswith("_bucket"):
                    le = s.labels.get("le") if s.labels else None
                    if le is None:
                        continue
                    bound = float("inf") if le == "+Inf" else float(le)
                    buckets[bound] = buckets.get(bound, 0.0) + float(s.value)
                elif n.endswith("_count"):
                    total_count = max(total_count, float(s.value))

        return buckets, total_count

    @staticmethod
    def _collect_histogram_samples(metric_name: str) -> Iterator[Metric]:
        """Return all metrics matching the given histogram name."""
        for metric in REGISTRY.collect():
            if getattr(metric, "name", None) == metric_name:
                yield metric

    @staticmethod
    def _compute_quantiles(
        sorted_bounds: list[tuple[float, float]],
        quantiles: tuple[float, ...],
        total: float,
    ) -> dict[str, float | None]:
        """
        Compute interpolated quantiles from cumulative bucket data.
        """
        result: dict[str, float | None] = {}
        for q in quantiles:
            rank = q * total
            prev_bound, prev_count = 0.0, 0.0
            value = None

            for upper_bound, cum in sorted_bounds:
                if rank <= cum:
                    in_bucket = cum - prev_count
                    if in_bucket > 0:
                        frac = (rank - prev_count) / in_bucket
                        value = prev_bound + frac * (upper_bound - prev_bound)
                    else:
                        value = upper_bound
                    break
                prev_bound, prev_count = upper_bound, cum

            result[f"p{int(q * 100)}"] = value
        return result

    # --------------------------------------------------------------------------
    # Event emission
    # --------------------------------------------------------------------------
    def emit_event(self, topic: str, payload: dict[str, Any]) -> None:
        """Emit an event record to logs and metrics sinks."""
        self._logger.info(
            f"[Observability] Event received: {topic}",
            extra={"attrs": payload},
        )
