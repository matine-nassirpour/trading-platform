import logging
import re
from typing import Final

from quantum.core.config.runtime.manager import ConfigManager
from quantum.infrastructure.observability.logging.constants import get_audit_allowlist

# Matches version suffixes such as "_v1", "_v2", "_v10" (case-insensitive)
_SUFFIX_VERSION_RE: Final[re.Pattern[str]] = re.compile(r"_v\d+$", re.IGNORECASE)


class AuditEventFilter(logging.Filter):
    """
    Filters audit events based on an explicit allow-list.
    Events must include an "event" dict with a non-empty "event_name" string.
    """

    def __init__(self) -> None:
        super().__init__()
        logging_settings = ConfigManager.load_logging()
        self._version = logging_settings.quantum_audit_events_version.lower()
        self._allowlist = get_audit_allowlist(self._version)

    def filter(self, record: logging.LogRecord) -> bool:
        """Return True if the record contains an allowed audit event."""
        ev = getattr(record, "event", None)
        if not isinstance(ev, dict):
            return False

        name = ev.get("event_name")
        if not isinstance(name, str) or not name:
            return False

        normalized = _SUFFIX_VERSION_RE.sub("", name.strip().lower())
        return normalized in self._allowlist
