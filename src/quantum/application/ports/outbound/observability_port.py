from typing import Protocol


class ObservabilityPort(Protocol):
    """Structural interface for querying observability data."""

    def initialize_observability(self) -> None:
        """Initialize logging, metrics, tracing, etc."""
        ...

    def ensure_run_id(self) -> str:
        """Generate or retrieve a unique runtime run_id."""
        ...

    def ensure_correlation_id(self) -> str:
        """
        Ensure a correlation ID is present in the current context.
        Returns the ID.
        """
        ...
