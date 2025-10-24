import logging
import re

from quantum.core.config.runtime.manager import ConfigManager
from quantum.infrastructure.observability.logging.constants import get_audit_allowlist

# Generic version suffix (eg: _v1, _v2, _v10)
_SUFFIX_VERSION_RE = re.compile(r"_v\d+$")


class AuditEventFilter(logging.Filter):
    def __init__(self) -> None:
        super().__init__()
        logging_settings = ConfigManager.load_logging()
        self._version = logging_settings.quantum_audit_events_version.lower()
        self._allow = get_audit_allowlist(self._version)

    def filter(self, record: logging.LogRecord) -> bool:
        ev = getattr(record, "event", None)
        if not isinstance(ev, dict):
            return False
        name = ev.get("event_name")
        if not isinstance(name, str) or not name:
            return False
        n = name.strip().lower()
        n = _SUFFIX_VERSION_RE.sub("", n)
        return n in self._allow
