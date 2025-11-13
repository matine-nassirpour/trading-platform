from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any, Protocol


class TraceHandle(Protocol):
    """
    Minimalistic, certifiable-safe handle representing an active trace span.

    This object is only used inside an async context manager and exposes:
      - `set_attribute`: to enrich the trace/log with key-value pairs.
      - `record_exception`: to attach an exception to the trace/log.
    """

    async def set_attribute(self, key: str, value: Any) -> None: ...
    async def record_exception(self, exc: BaseException) -> None: ...
    async def end(self) -> None: ...


class TracingPort(ABC):
    """
    Clean Architecture tracing abstraction.

    Provides hybrid observability:
      - OTEL spans (if enabled)
      - Structured logs (always)
      - Failure recording (span error + structured log + audit event)

    All methods are async by design to integrate naturally with orchestrators.
    """

    @abstractmethod
    async def trace(
        self,
        operation: str,
        /,
        *,
        attributes: Mapping[str, Any] | None = None,
    ) -> TraceHandle:
        """Return an async context manager opening a hybrid span."""

    @abstractmethod
    async def record_failure(
        self,
        operation: str,
        exc: BaseException,
        /,
        *,
        attributes: Mapping[str, Any] | None = None,
    ) -> None:
        """
        Hybrid error reporting:
            - span.set_status(ERROR)
            - span.record_exception()
            - structured error log
            - audit event (immutable)
        """
        ...
