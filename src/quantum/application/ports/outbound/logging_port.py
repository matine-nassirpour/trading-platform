from typing import Protocol


class LoggingPort(Protocol):
    """Structural interface for log emission and retrieval."""

    def emit_info(self, message: str, **attrs: object) -> None:
        """Emit a structured INFO-level log message."""
        ...

    def emit_event(self, payload: dict[str, object]) -> None:
        """Emit a structured audit event (schema-validated)."""
        ...
