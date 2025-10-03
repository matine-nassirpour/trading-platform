import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from quantum.infrastructure.observability.logging._io_utils import (
    fsync_dir,
    inc_disk_error_counter,
    safe_unlink,
)
from quantum.shared.time.naming import generate_audit_blob_name


class AuditEventFileHandler(logging.Handler):
    """
    Writes selected *event* payloads (record.extra['event']) as separate JSON files:
    <base>/<env>/<namespace>/<app>/<YYYY>/<MM>/<DD>/<HHMMSS-UUID>.json

    Use to persist *critical* trading events individually.
    Activate via QUANTUM_AUDIT_DIR.
    """

    def __init__(
        self,
        base_dir: str,
        app: str,
        environment: str,
        namespace: str,
        encoding: str = "utf-8",
    ) -> None:
        super().__init__()
        self.base_dir = Path(base_dir)
        self.app = app
        self.environment = environment
        self.namespace = namespace
        self.encoding = encoding

    def emit(self, record: logging.LogRecord) -> None:
        event = getattr(record, "event", None)
        if not isinstance(event, dict):  # only care about structured trading events
            return

        # 1) Path resolution and directory creation
        try:
            dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
            blob_name = generate_audit_blob_name(now=dt)
            path = (
                self.base_dir / self.environment / self.namespace / self.app / blob_name
            )
            path.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            inc_disk_error_counter()
            self.handleError(record)
            return

        # 2) Atomic write + fsync file + fsync parent directory
        tmp_path: Path | None = None
        try:
            tmp_path = path.with_suffix(".json.tmp")
            with open(tmp_path, "w", encoding=self.encoding, newline="\n") as f:
                json.dump(
                    event, f, ensure_ascii=False, separators=(",", ":"), allow_nan=False
                )
                f.flush()
                os.fsync(f.fileno())

            os.replace(tmp_path, path)  # atomic move
            fsync_dir(path.parent)  # ensure directory entry is durable
        except (OSError, TypeError, ValueError):
            inc_disk_error_counter()
            # Best-effort cleanup of tmp file
            safe_unlink(tmp_path)
            self.handleError(record)
