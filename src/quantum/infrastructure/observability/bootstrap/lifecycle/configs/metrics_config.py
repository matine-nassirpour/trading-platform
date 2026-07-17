from dataclasses import dataclass


@dataclass(frozen=True)
class MetricsConfig:
    """
    Immutable value object used by MetricsInitializer.

    Defines the behavior of the Prometheus HTTP endpoint.
    """

    host: str
    port: int
