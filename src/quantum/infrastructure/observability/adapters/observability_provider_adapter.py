from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from prometheus_client import REGISTRY

from quantum.application.ports.outbound.observability_port import ObservabilityPort
from quantum.infrastructure.observability.bootstrap.init_manager import (
    init_observability,
)
from quantum.infrastructure.observability.context.run_id import (
    generate_run_id,
    get_run_id,
)


class ObservabilityProviderAdapter(ObservabilityPort):
    """Concrete adapter implementing observability access and telemetry control."""

    def __init__(self) -> None:
        self._logger = logging.getLogger("quantum.observability.adapter")

    # --------------------------------------------------------------------------
    # Lifecycle
    # --------------------------------------------------------------------------
    def initialize_observability(self) -> None:
        """Initialize the observability stack (logging, metrics, tracing, etc.)."""
        init_observability()

    def ensure_run_id(self) -> str:
        """Ensure a unique run_id is available for the current process."""
        rid = get_run_id()
        if not rid:
            rid = generate_run_id()
        return rid

    # --------------------------------------------------------------------------
    # Metrics access (Prometheus REGISTRY)
    # --------------------------------------------------------------------------
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
            buckets: dict[float, float] = {}
            total_count = 0.0

            for metric in REGISTRY.collect():
                if getattr(metric, "name", None) != metric_name:
                    continue
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

            sorted_bounds = sorted(buckets.items(), key=lambda kv: kv[0])
            total = total_count or (sorted_bounds[-1][1] if sorted_bounds else 0.0)
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
        except Exception as exc:
            self._logger.debug("Failed to compute histogram quantiles: %s", exc)
            return {f"p{int(q * 100)}": None for q in quantiles}
