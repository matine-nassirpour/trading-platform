from __future__ import annotations

import io
import json
import logging
import os
import sys

from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from quantum.infrastructure.observability.logging.config_bundle import (
    LoggingRuntimeBundle,
)
from quantum.infrastructure.observability.logging.exception_processor import (
    ExceptionProcessor,
)
from quantum.infrastructure.observability.logging.utils._io_utils import fsync_dir
from quantum.infrastructure.observability.metrics.collectors.health_collector import (
    logging_disk_errors_total,
    logging_file_rotations_total,
)
from quantum.infrastructure.time.naming import partition_path_components


class PartitionedJSONLFileHandler(logging.Handler):
    """
    Thread-safe file handler that writes JSONL log entries into
    partitioned, rotating files with on-disk durability guarantees.

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

    _EVENTS_PREFIX: Final[str] = "events"
    _BAD_PREFIX: Final[str] = "bad-logs"
    _EXT: Final[str] = ".jsonl"

    def __init__(
        self, *, bundle: LoggingRuntimeBundle, encoding: str = "utf-8"
    ) -> None:
        super().__init__()
        self._bundle = bundle
        self._encoding = encoding
        self._base_dir = Path(bundle.log_dir)

        self._current_path: Path | None = None
        self._bad_path: Path | None = None
        self._fh: io.TextIOWrapper | None = None
        self._bad_fh: io.TextIOWrapper | None = None

        self._fsync = self._bundle.log_fsync
        self._max_bytes = self._bundle.log_max_bytes
        self._warn_bytes = self._bundle.log_warn_bytes

        self._part_index = 0
        self._warned_this_part = False

    @property
    def base_dir(self) -> Path:
        """Expose base directory for external health checks or probes."""
        return self._base_dir

    # --------------------------------------------------------------------------
    # Core pipeline
    # --------------------------------------------------------------------------
    def emit(self, record: logging.LogRecord) -> None:
        """
        Appends a JSON log entry to the current partition file,
        creating or rotating files as necessary.
        """
        self.acquire()
        try:
            dir_path, file_path, bad_path = self._resolve_partition(record)
            if file_path != self._current_path:
                self._reopen_partition(file_path, bad_path)

            self._write_record(record)
            if self._max_bytes > 0:
                self._check_rollover(record)
        finally:
            self.release()

    # --------------------------------------------------------------------------
    # Internal helpers
    # --------------------------------------------------------------------------
    def _resolve_partition(self, record: logging.LogRecord) -> tuple[Path, Path, Path]:
        """Determines the partition directory and file paths for the record."""
        try:
            dt = datetime.fromtimestamp(record.created, tz=UTC)
            yyyy, mm, dd, hh = partition_path_components(dt)
            dir_path = (
                self._base_dir
                / self._bundle.env
                / self._bundle.namespace
                / self._bundle.app_name
                / yyyy
                / mm
                / dd
                / hh
            )

            file_path = dir_path / self._events_filename(
                yyyy, mm, dd, hh, self._part_index
            )
            bad_path = dir_path / self._bad_filename(yyyy, mm, dd, hh, self._part_index)

            if self._current_path is None or self._current_path.parent != dir_path:
                self._part_index = 0
                file_path = dir_path / self._events_filename(yyyy, mm, dd, hh, 0)
                bad_path = dir_path / self._bad_filename(yyyy, mm, dd, hh, 0)

            return dir_path, file_path, bad_path
        except Exception:
            logging_disk_errors_total.inc()
            self.handleError(record)
            raise

    def _write_record(self, record: logging.LogRecord) -> None:
        """Formats and writes a single log record to the main file, with quarantine fallback."""
        try:
            msg = self.format(record)
            if not self._fh:
                raise OSError("File handle not available")
            self._fh.write(msg + "\n")
            self._flush(self._fh)
        except Exception as e:
            self._write_quarantine(record, e)

    def _write_quarantine(self, record: logging.LogRecord, error: Exception) -> None:
        """Writes malformed log records into a quarantine file for forensic review."""
        try:
            if not self._bad_fh:
                raise OSError("Quarantine file not available")

            # Unified exception block (etype/evalue/tb from *error*, not record)
            try:
                # Extract exception info from the failure that triggered quarantine
                etype = type(error)
                evalue = error
                tb = error.__traceback__
                exc_block = ExceptionProcessor.extract(
                    type("DummyRecord", (), {"exc_info": (etype, evalue, tb)})
                )
            except Exception:
                exc_block = {
                    "exception": "quarantine exception extraction failed",
                    "exception_type": "Exception",
                    "exception_message": None,
                    "exception_stacktrace": None,
                }

            # Build a forensic entry — no schema, no Pydantic, no strict formatting.
            safe_entry = {
                "error": "log_record_formatting_failed",
                "reason": str(error),
                "logger": getattr(record, "name", None),
                "level": getattr(record, "levelname", None),
                "created": getattr(record, "created", None),
                # Stable unified exception block from the processor
                "exception": exc_block.get("exception"),
                "exception_type": exc_block.get("exception_type"),
                "exception_message": exc_block.get("exception_message"),
                "exception_stacktrace": exc_block.get("exception_stacktrace"),
                # Always try to capture the raw message
                "raw_message": None,
            }

            try:
                safe_entry["raw_message"] = record.getMessage()
            except Exception:
                safe_entry["raw_message"] = "<raw_message_unavailable>"

            self._bad_fh.write(
                json.dumps(safe_entry, ensure_ascii=False, separators=(",", ":")) + "\n"
            )
            self._flush(self._bad_fh)

        except Exception:
            logging_disk_errors_total.inc()
            self.handleError(record)

    def _flush(self, fh: io.TextIOWrapper) -> None:
        """Flushes the provided file handle, optionally fsyncing to disk."""
        fh.flush()
        if self._fsync:
            try:
                os.fsync(fh.fileno())
            except OSError:
                logging_disk_errors_total.inc()

    def _check_rollover(self, record: logging.LogRecord) -> None:
        """Performs size-based rollover, emitting warnings and rotation metrics."""
        try:
            size = self._fh.tell() if self._fh else 0
            if (
                self._warn_bytes
                and size >= self._warn_bytes
                and not self._warned_this_part
            ):
                sys.stderr.write(
                    f"[quantum.logs] nearing threshold: {self._current_path} "
                    f"size={size} warn_bytes={self._warn_bytes}\n"
                )
                sys.stderr.flush()
                self._warned_this_part = True

            if size >= self._max_bytes:
                self._part_index += 1
                dt = datetime.fromtimestamp(record.created, tz=UTC)
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
                self._reopen_partition(next_file, next_bad)

                self._warned_this_part = False
                if logging_file_rotations_total:
                    with suppress(Exception):
                        logging_file_rotations_total.inc()
        except Exception:
            logging_disk_errors_total.inc()

    def _reopen_partition(self, path: Path, bad_path: Path) -> None:
        """Reopens partition files safely, ensuring directories exist and flushing prior handles."""
        for fh in (self._fh, self._bad_fh):
            with suppress(OSError, ValueError):
                if fh:
                    fh.flush()
                    fh.close()

        path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = open(path, "a", encoding=self._encoding, newline="\n")
        self._bad_fh = open(bad_path, "a", encoding=self._encoding, newline="\n")
        self._current_path = path
        self._bad_path = bad_path

        fsync_dir(path.parent)
        self._warned_this_part = False

    def close(self) -> None:
        """Closes all open file handles safely."""
        self.acquire()
        try:
            for fh in (self._fh, self._bad_fh):
                with suppress(Exception):
                    if fh:
                        fh.flush()
                        fh.close()
            self._fh = None
            self._bad_fh = None
            self._current_path = None
            self._bad_path = None
        finally:
            self.release()
        super().close()

    # --------------------------------------------------------------------------
    # Naming utilities
    # --------------------------------------------------------------------------
    @staticmethod
    def _events_filename(yyyy: str, mm: str, dd: str, hh: str, part: int) -> str:
        suffix = f".part{part}" if part > 0 else ""
        return f"{PartitionedJSONLFileHandler._EVENTS_PREFIX}-{yyyy}{mm}{dd}-{hh}{suffix}{PartitionedJSONLFileHandler._EXT}"

    @staticmethod
    def _bad_filename(yyyy: str, mm: str, dd: str, hh: str, part: int) -> str:
        suffix = f".part{part}" if part > 0 else ""
        return f"{PartitionedJSONLFileHandler._BAD_PREFIX}-{yyyy}{mm}{dd}-{hh}{suffix}{PartitionedJSONLFileHandler._EXT}"
