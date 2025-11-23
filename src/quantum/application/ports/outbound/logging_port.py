from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LoggingPort(Protocol):
    """Hexagonal outbound port for structured, safety-grade logging."""

    def info(self, message: str, *, attrs: Mapping[str, Any] | None = None) -> None:
        """Emit an INFO-level structured log."""
        ...

    def log(
        self,
        level: int,
        message: str,
        *,
        attrs: Mapping[str, Any] | None = None,
    ) -> None:
        """Generic structured log emission for dynamic/logical levels."""
        ...

    def emit_event(self, payload: Mapping[str, Any]) -> None:
        """Emit a structured audit event."""
        ...
