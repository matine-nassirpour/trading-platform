from __future__ import annotations

import time

from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass, field


@dataclass(slots=True)
class OrchestrationContext:
    """Immutable logical context for a single orchestration flow.

    This context is designed to:
        - provide a stable correlation id for logs, metrics and tracing,
        - track temporal information (start time, attempt count),
        - carry optional metadata for audit & governance.

    The context is intentionally lightweight and serializable.
    """

    correlation_id: str
    started_at_epoch_s: float
    attempt: int = 1
    metadata: Mapping[str, str] = field(default_factory=dict)

    @classmethod
    def start_new(
        cls,
        *,
        correlation_id: str,
        metadata: Mapping[str, str] | None = None,
    ) -> OrchestrationContext:
        """Create a new orchestration context for a fresh request."""
        return cls(
            correlation_id=correlation_id,
            started_at_epoch_s=time.time(),
            attempt=1,
            metadata=dict(metadata or {}),
        )

    def with_attempt(self, attempt: int) -> OrchestrationContext:
        """Return a new context with an updated attempt count."""
        if attempt < 1:
            raise ValueError("attempt must be >= 1")
        return OrchestrationContext(
            correlation_id=self.correlation_id,
            started_at_epoch_s=self.started_at_epoch_s,
            attempt=attempt,
            metadata=self.metadata,
        )

    def with_metadata(
        self,
        **extra: str,
    ) -> OrchestrationContext:
        """Return a new context with additional metadata keys."""
        merged: MutableMapping[str, str] = dict(self.metadata)
        merged.update(extra)
        return OrchestrationContext(
            correlation_id=self.correlation_id,
            started_at_epoch_s=self.started_at_epoch_s,
            attempt=self.attempt,
            metadata=merged,
        )

    @property
    def age_s(self) -> float:
        """Elapsed time since orchestration started (seconds)."""
        return max(0.0, time.time() - self.started_at_epoch_s)
