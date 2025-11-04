from collections.abc import Mapping
from typing import Any, Protocol


class ObservabilityPort(Protocol):
    """Structural interface for querying observability data."""

    def initialize_observability(self) -> None:
        """Initialize logging, metrics, tracing, etc."""
        ...

    def ensure_run_id(self) -> None:
        """Generate or retrieve a unique runtime run_id."""
        ...

    def collect_metrics(self) -> list[Mapping[str, Any]]:
        """Return all currently registered metrics as a serializable collection."""
        ...

    def get_gauge_value(self, name: str) -> float | None:
        """Return the numeric value of a gauge metric, or None if unavailable."""
        ...

    def get_counter_value(self, name: str) -> float | None:
        """Return the numeric value of a counter metric, or None if unavailable."""
        ...

    def get_histogram_quantiles(
        self,
        metric_name: str,
        quantiles: tuple[float, ...] = (0.5, 0.95, 0.99),
    ) -> dict[str, float | None]:
        """Compute approximate quantiles for a histogram metric."""
        ...
