import json
import logging
import os

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

from quantum.infrastructure.observability.logging.utils._io_utils import (
    fsync_dir,
    safe_unlink,
)
from quantum.infrastructure.observability.logging.utils.naming import (
    generate_audit_blob_name,
)
from quantum.infrastructure.observability.metrics.collectors.health_collector import (
    logging_disk_errors_total,
)


class AuditEventFileHandler(logging.Handler):
    """
    Writes structured audit events as individual JSON files.
    """

    _TMP_SUFFIX: Final[str] = ".json.tmp"
    _FINAL_SUFFIX: Final[str] = ".json"

    def __init__(
        self,
        base_dir: str,
        env: str,
        namespace: str,
        app: str,
        *,
        encoding: str = "utf-8",
    ) -> None:
        super().__init__()
        self._base_dir = Path(base_dir)
        self._env = env
        self._namespace = namespace
        self._app = app
        self._encoding = encoding

    @property
    def base_dir(self) -> Path:
        """Expose base directory for external health checks or probes."""
        return self._base_dir

    # --------------------------------------------------------------------------
    # Core pipeline
    # --------------------------------------------------------------------------
    def emit(self, record: logging.LogRecord) -> None:
        """
        Persists the event payload associated with this log record, if any.
        The record must include an 'event' dict attribute; otherwise, it is ignored.
        """
        event = getattr(record, "event", None)
        if not isinstance(event, dict):
            return

        try:
            path = self._resolve_event_path(record)
        except OSError:
            logging_disk_errors_total.inc()
            self.handleError(record)
            return

        self._write_atomic_json(event, path, record)

    # --------------------------------------------------------------------------
    # Internal Helpers
    # --------------------------------------------------------------------------
    def _resolve_event_path(self, record: logging.LogRecord) -> Path:
        """
        Computes the target file path for the given record timestamp.
        Ensures that the parent directories exist.
        """
        dt = datetime.fromtimestamp(record.created, tz=UTC)
        blob_name = generate_audit_blob_name(now=dt)
        path = self._base_dir / self._env / self._namespace / self._app / blob_name
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _write_atomic_json(
        self, event: dict[str, Any], path: Path, record: logging.LogRecord
    ) -> None:
        """
        Writes the given event dictionary atomically to the specified path.
        Includes fsync() on both file and directory, and cleans up on failure.
        """
        tmp_path: Path | None = None
        try:
            tmp_path = path.with_suffix(self._TMP_SUFFIX)
            with open(tmp_path, "w", encoding=self._encoding, newline="\n") as f:
                json.dump(
                    event, f, ensure_ascii=False, separators=(",", ":"), allow_nan=False
                )
                f.flush()
                os.fsync(f.fileno())

            os.replace(tmp_path, path)  # Atomic move
            fsync_dir(path.parent)
        except (OSError, TypeError, ValueError):
            logging_disk_errors_total.inc()
            if tmp_path is not None:
                safe_unlink(tmp_path)
            self.handleError(record)
