import logging
import re

from typing import Final

# Matches version suffixes such as "_v1", "_v2", "_v10" (case-insensitive)
_SUFFIX_RE: Final[re.Pattern[str]] = re.compile(r"_v\d+$", re.IGNORECASE)


class AuditEventFilter(logging.Filter):
    """
    Filters audit events based on an explicit allow-list.
    Events must include an "event" dict with a non-empty "event_name" string.
    """

    def __init__(self, *, allowlist: set[str]) -> None:
        super().__init__()
        self._allowlist = allowlist

    def filter(self, record: logging.LogRecord) -> bool:
        """Return True if the record contains an allowed audit event."""
        ev = getattr(record, "event", None)
        if not isinstance(ev, dict):
            return False

        name = ev.get("event_name")
        if not isinstance(name, str) or not name:
            return False

        normalized = _SUFFIX_RE.sub("", name.strip().lower())
        return normalized in self._allowlist
