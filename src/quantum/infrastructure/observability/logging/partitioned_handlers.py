import io
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from quantum.shared.time.naming import partition_path_components


class PartitionedJSONLFileHandler(logging.Handler):
    """
    Writes JSON logs to partitioned JSONL files:
    <base>/<env>/<namespace>/<app>/<YYYY>/<MM>/<DD>/<HH>/events-YYYYMMDD-HH.jsonl
    Quarantines malformed lines to: .../bad-logs-YYYYMMDD-HH.jsonl
    Optional fsync per write with QUANTUM_LOG_FSYNC=1

    Thread-safety:
      - All state mutations and writes are protected by the base Handler lock
        via self.acquire()/self.release().
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

        self._current_path: Path | None = None
        self._bad_path: Path | None = None
        self._fh: io.TextIOWrapper | None = None
        self._bad_fh: io.TextIOWrapper | None = None
        self._fsync = os.getenv("QUANTUM_LOG_FSYNC", "0") == "1"

    def emit(self, record: logging.LogRecord) -> None:
        self.acquire()
        try:
            # Compute partition paths for this record's hour
            try:
                dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
                yyyy, mm, dd, hh = partition_path_components(dt)
                dir_path = (
                    self.base_dir
                    / self.environment
                    / self.namespace
                    / self.app
                    / yyyy
                    / mm
                    / dd
                    / hh
                )
                file_path = dir_path / f"events-{yyyy}{mm}{dd}-{hh}.jsonl"
                bad_path = dir_path / f"bad-logs-{yyyy}{mm}{dd}-{hh}.jsonl"
                if file_path != self._current_path:
                    self._reopen(file_path, bad_path)
            except (OSError, ValueError):
                self.handleError(record)
                return

            # Try to format, otherwise quarantine
            try:
                msg = self.format(record)
                assert self._fh is not None
                self._fh.write(msg + "\n")
                if self._fsync:
                    self._fh.flush()
                    os.fsync(self._fh.fileno())
                else:
                    self._fh.flush()
            except (OSError, ValueError, TypeError) as e:
                try:
                    assert self._bad_fh is not None
                    safe = {
                        "error": "formatting_failed",
                        "reason": str(e),
                        "logger": getattr(record, "name", "?"),
                        "level": getattr(record, "levelname", "?"),
                        "created": getattr(record, "created", 0),
                        "raw_message": None,
                    }
                    try:
                        safe["raw_message"] = record.getMessage()
                    except (ValueError, TypeError, AttributeError):
                        safe["raw_message"] = None
                    self._bad_fh.write(
                        json.dumps(safe, ensure_ascii=False, separators=(",", ":"))
                        + "\n"
                    )
                    self._bad_fh.flush()
                except (OSError, ValueError, TypeError):
                    self.handleError(record)
        finally:
            self.release()

    def _reopen(self, path: Path, bad_path: Path) -> None:
        """
        (Lock must already be held by caller.)
        Close previous files and open (or create) the partition files for the new hour.
        """
        # Close previous files (best-effort)
        for fh in (self._fh, self._bad_fh):
            if fh:
                try:
                    fh.flush()
                    fh.close()
                except (OSError, ValueError):
                    pass

        # Prepare directory and open new files
        path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = open(path, "a", encoding=self.encoding, newline="\n")
        self._bad_fh = open(bad_path, "a", encoding=self.encoding, newline="\n")
        self._current_path = path
        self._bad_path = bad_path

    def close(self) -> None:
        self.acquire()
        try:
            for fh in (self._fh, self._bad_fh):
                try:
                    if fh:
                        fh.flush()
                        fh.close()
                except (OSError, ValueError):
                    pass
            self._fh = None
            self._bad_fh = None
            self._current_path = None
            self._bad_path = None
        finally:
            self.release()
        super().close()
