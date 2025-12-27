from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AggregateRoot:
    """
    Marker base class for all Aggregate Roots.
    Enforces immutability-by-design.
    """
