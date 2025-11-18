import logging

from collections.abc import Mapping

from quantum.infrastructure.observability.logging.audit.allowlist import (
    normalize_event_name,
    validate_event_name,
)


class AuditEventFilter(logging.Filter):
    """Filters audit events based on an explicit allow-list."""

    def __init__(self, *, allowlist: set[str]) -> None:
        super().__init__()
        self._allowlist = allowlist

    def filter(self, record: logging.LogRecord) -> bool:
        """Return True if the record contains an allowed audit event."""

        event = getattr(record, "event", None)
        if not isinstance(event, Mapping):
            return False

        name = event.get("event_name")
        if not isinstance(name, str) or not name.strip():
            return False

        try:
            normalized = normalize_event_name(name)
            validate_event_name(normalized)
        except Exception:
            return False

        return normalized in self._allowlist
