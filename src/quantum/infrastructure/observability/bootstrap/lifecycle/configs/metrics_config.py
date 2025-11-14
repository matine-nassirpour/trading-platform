from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MetricsConfig:
    """
    Immutable value object used by MetricsInitializer.

    Defines the behavior of the Prometheus HTTP endpoint.
    """

    host: str  # ex: "0.0.0.0"
    port: int  # ex: 9090
    enabled: bool  # port <= 0 → disabled
