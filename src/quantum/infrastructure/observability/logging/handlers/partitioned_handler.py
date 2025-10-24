import io
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from quantum.core.config.models.core import CoreSettings
from quantum.core.config.models.logging import LoggingSettings
from quantum.infrastructure.observability.logging._io_utils import (
    fsync_dir,
    inc_disk_error_counter,
)
from quantum.shared.time.naming import partition_path_components

try:
    from quantum.infrastructure.observability.metrics.collectors.health_collector import (
        logging_file_rotations_total,
    )
except (ModuleNotFoundError, ImportError):
    logging_file_rotations_total = None


class PartitionedJSONLFileHandler(logging.Handler):
    """
    Writes JSON logs to partitioned JSONL files.

    Path pattern:
        <base>/<env>/<namespace>/<app>/<YYYY>/<MM>/<DD>/<HH>/events-YYYYMMDD-HH[.partN].jsonl

    Malformed entries are quarantined to:
        bad-logs-YYYYMMDD-HH[.partN].jsonl

    Features:
        - Optional fsync per write.
        - Optional size-based rollover with warning threshold.
        - Thread-safe (Handler lock).
        - Fully decoupled from environment variables.
    """

    def __init__(
        self,
        settings: CoreSettings,
        observability: LoggingSettings,
        *,
        encoding: str = "utf-8",
    ) -> None:
        super().__init__()
        self._settings = settings
        self._cfg = observability
        self._encoding = encoding

        base_dir = observability.quantum_log_dir or "./logs"
        self._base_dir = Path(base_dir)

        self._current_path: Path | None = None
        self._bad_path: Path | None = None
        self._fh: io.TextIOWrapper | None = None
        self._bad_fh: io.TextIOWrapper | None = None

        self._fsync = observability.quantum_log_fsync
        self._max_bytes = observability.quantum_log_max_bytes
        self._warn_bytes = observability.quantum_log_warn_bytes or 0

        self._part_index = 0
        self._warned_this_part = False

    @property
    def base_dir(self) -> Path:
        """
        Return the base directory of this handler for health/probe inspection.
        Exposed explicitly to allow external components (like observability probes)
        to assess writability and persistence status in a decoupled manner.
        """
        return self._base_dir

    # ─── Core API
    def emit(self, record: logging.LogRecord) -> None:
        self.acquire()
        try:
            # 1) Resolve partition (by record time)
            try:
                dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
                yyyy, mm, dd, hh = partition_path_components(dt)
                dir_path = (
                    self._base_dir
                    / self._settings.quantum_env
                    / self._settings.quantum_ns
                    / self._settings.quantum_app_name
                    / yyyy
                    / mm
                    / dd
                    / hh
                )

                file_path = dir_path / self._events_filename(
                    yyyy, mm, dd, hh, self._part_index
                )
                bad_path = dir_path / self._bad_filename(
                    yyyy, mm, dd, hh, self._part_index
                )

                # detect partition (hourly) change
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

            except Exception:
                inc_disk_error_counter()
                self.handleError(record)
                return

            # 2) Write formatted JSON line
            try:
                msg = self.format(record)
                assert self._fh is not None
                self._fh.write(msg + "\n")
                self._flush(self._fh)
            except Exception as e:
                self._write_quarantine(record, e)

            # 3) Rollover by file size (if configured)
            if self._max_bytes > 0 and self._fh is not None:
                self._check_rollover(record)

        finally:
            self.release()

    # ─── Internal helpers
    def _write_quarantine(self, record: logging.LogRecord, error: Exception) -> None:
        """Safely writes malformed log records to the quarantine file."""
        try:
            assert self._bad_fh is not None
            safe_entry = {
                "error": "formatting_failed",
                "reason": str(error),
                "logger": getattr(record, "name", "?"),
                "level": getattr(record, "levelname", "?"),
                "created": getattr(record, "created", 0),
                "raw_message": None,
            }
            try:
                safe_entry["raw_message"] = record.getMessage()
            except Exception:
                pass
            self._bad_fh.write(
                json.dumps(safe_entry, ensure_ascii=False, separators=(",", ":")) + "\n"
            )
            self._flush(self._bad_fh)
        except Exception:
            inc_disk_error_counter()
            self.handleError(record)

    def _check_rollover(self, record: logging.LogRecord) -> None:
        """Rollover logic with warning thresholds."""
        try:
            size = self._fh.tell() if self._fh else 0
            if (
                self._warn_bytes
                and size >= self._warn_bytes
                and not self._warned_this_part
            ):
                sys.stderr.write(
                    f"[quantum.logs] nearing size threshold: "
                    f"path={self._current_path} size={size} warn_bytes={self._warn_bytes}\n"
                )
                sys.stderr.flush()
                self._warned_this_part = True

            if size >= self._max_bytes:
                self._part_index += 1
                dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
                yyyy, mm, dd, hh = partition_path_components(dt)
                dir_path = (
                    self._current_path.parent if self._current_path else self._base_dir
                )
                next_file = dir_path / self._events_filename(
                    yyyy, mm, dd, hh, self._part_index
                )
                next_bad = dir_path / self._bad_filename(
                    yyyy, mm, dd, hh, self._part_index
                )
                self._reopen(next_file, next_bad)
                self._warned_this_part = False
                if logging_file_rotations_total:
                    try:
                        logging_file_rotations_total.inc()
                    except Exception:
                        pass
        except Exception:
            inc_disk_error_counter()

    def _flush(self, fh: io.TextIOWrapper) -> None:
        fh.flush()
        if self._fsync:
            try:
                os.fsync(fh.fileno())
            except OSError:
                inc_disk_error_counter()

    def _reopen(self, path: Path, bad_path: Path) -> None:
        """Reopen partition files safely."""
        for fh in (self._fh, self._bad_fh):
            try:
                if fh:
                    fh.flush()
                    fh.close()
            except (OSError, ValueError):
                pass

        path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = open(path, "a", encoding=self._encoding, newline="\n")
        self._bad_fh = open(bad_path, "a", encoding=self._encoding, newline="\n")
        self._current_path = path
        self._bad_path = bad_path
        fsync_dir(path.parent)
        self._warned_this_part = False

    def close(self) -> None:
        self.acquire()
        try:
            for fh in (self._fh, self._bad_fh):
                try:
                    if fh:
                        fh.flush()
                        fh.close()
                except Exception:
                    pass
            self._fh = None
            self._bad_fh = None
            self._current_path = None
            self._bad_path = None
        finally:
            self.release()
        super().close()

    # ─── Naming
    @staticmethod
    def _events_filename(yyyy: str, mm: str, dd: str, hh: str, part: int) -> str:
        suffix = f".part{part}" if part > 0 else ""
        return f"events-{yyyy}{mm}{dd}-{hh}{suffix}.jsonl"

    @staticmethod
    def _bad_filename(yyyy: str, mm: str, dd: str, hh: str, part: int) -> str:
        suffix = f".part{part}" if part > 0 else ""
        return f"bad-logs-{yyyy}{mm}{dd}-{hh}{suffix}.jsonl"
