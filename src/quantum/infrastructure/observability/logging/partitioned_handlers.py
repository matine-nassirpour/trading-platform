import io
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from quantum.infrastructure.observability.logging._io_utils import (
    fsync_dir,
    inc_disk_error_counter,
)
from quantum.shared.time.naming import partition_path_components

# Best-effort
try:
    from quantum.infrastructure.observability.metrics.health import (
        logging_file_rotations_total,
    )
except Exception:
    logging_file_rotations_total = None  # type: ignore


class PartitionedJSONLFileHandler(logging.Handler):
    """
    Writes JSON logs to partitioned JSONL files:
    <base>/<env>/<namespace>/<app>/<YYYY>/<MM>/<DD>/<HH>/events-YYYYMMDD-HH[.partN].jsonl
    Quarantines malformed lines: .../bad-logs-YYYYMMDD-HH[.partN].jsonl
    Optional fsync per write with QUANTUM_LOG_FSYNC=1
    Optional rollover by size with QUANTUM_LOG_MAX_BYTES
    Thread-safe via Handler lock.
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

        # Rollover config
        try:
            self._max_bytes = int(os.getenv("QUANTUM_LOG_MAX_BYTES", "0") or "0")
        except (TypeError, ValueError):
            self._max_bytes = 0
        try:
            self._warn_bytes = int(os.getenv("QUANTUM_LOG_WARN_BYTES", "0") or "0")
        except (TypeError, ValueError):
            self._warn_bytes = 0

        self._part_index: int = 0  # Part index within the same hour

    def emit(self, record: logging.LogRecord) -> None:
        self.acquire()
        try:
            # 1) Resolve partition (by record time)
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
                # build target paths for current part index
                file_path = dir_path / self._events_filename(
                    yyyy, mm, dd, hh, self._part_index
                )
                bad_path = dir_path / self._bad_filename(
                    yyyy, mm, dd, hh, self._part_index
                )

                # hour changed? reset part index to 0
                if self._current_path is None or self._current_path.parent != dir_path:
                    self._part_index = 0
                    file_path = dir_path / self._events_filename(
                        yyyy, mm, dd, hh, self._part_index
                    )
                    bad_path = dir_path / self._bad_filename(
                        yyyy, mm, dd, hh, self._part_index
                    )

                if file_path != self._current_path:
                    self._reopen(file_path, bad_path)
            except (OSError, ValueError):
                inc_disk_error_counter()
                self.handleError(record)
                return

            # 2) Write
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
                # quarantine
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
                    except Exception:
                        safe["raw_message"] = None
                    self._bad_fh.write(
                        json.dumps(safe, ensure_ascii=False, separators=(",", ":"))
                        + "\n"
                    )
                    if self._fsync:
                        self._bad_fh.flush()
                        os.fsync(self._bad_fh.fileno())
                    else:
                        self._bad_fh.flush()
                except (OSError, ValueError, TypeError):
                    inc_disk_error_counter()
                    self.handleError(record)
                    return

            # 3) Rollover by size (best effort, post-write)
            if self._max_bytes > 0 and self._fh is not None:
                try:
                    size = os.fstat(self._fh.fileno()).st_size
                    if self._warn_bytes and size >= self._warn_bytes:
                        logging.getLogger(__name__).warning(
                            "log file nearing size threshold",
                            extra={
                                "attrs": {
                                    "path": str(self._current_path),
                                    "size": size,
                                    "warn_bytes": self._warn_bytes,
                                }
                            },
                        )
                    if size >= self._max_bytes:
                        self._part_index += 1
                        yyyy, mm, dd, hh = partition_path_components(
                            datetime.fromtimestamp(record.created, tz=timezone.utc)
                        )
                        dir_path = self._current_path.parent  # same hour directory
                        next_file = dir_path / self._events_filename(
                            yyyy, mm, dd, hh, self._part_index
                        )
                        next_bad = dir_path / self._bad_filename(
                            yyyy, mm, dd, hh, self._part_index
                        )
                        self._reopen(next_file, next_bad)
                        if logging_file_rotations_total:
                            try:
                                logging_file_rotations_total.inc()
                            except Exception:
                                pass
                except Exception:
                    # Rollover errors should not interrupt the pipeline
                    inc_disk_error_counter()
                    # we leave the current file active
        finally:
            self.release()

    @staticmethod
    def _events_filename(yyyy: str, mm: str, dd: str, hh: str, part: int) -> str:
        return f"events-{yyyy}{mm}{dd}-{hh}{''.join(['.part', str(part)] if part > 0 else '')}.jsonl"

    @staticmethod
    def _bad_filename(yyyy: str, mm: str, dd: str, hh: str, part: int) -> str:
        return f"bad-logs-{yyyy}{mm}{dd}-{hh}{''.join(['.part', str(part)] if part > 0 else '')}.jsonl"

    def _reopen(self, path: Path, bad_path: Path) -> None:
        # close previous
        for fh in (self._fh, self._bad_fh):
            if fh:
                try:
                    fh.flush()
                    fh.close()
                except (OSError, ValueError):
                    pass
        path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = open(path, "a", encoding=self.encoding, newline="\n")
        self._bad_fh = open(bad_path, "a", encoding=self.encoding, newline="\n")
        self._current_path = path
        self._bad_path = bad_path
        fsync_dir(path.parent)

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
