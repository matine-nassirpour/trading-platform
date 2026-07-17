import json
import logging
import threading

from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from quantum.infrastructure.observability.foundation.metrics.c0_metric_registry import (
    define_counter,
)
from quantum.infrastructure.observability.foundation.system_diagnostics.c0_diagnostic_logger import (
    get_diagnostic_logger,
)
from quantum.infrastructure.observability.logging.sinks.filesystem.naming import (
    generate_audit_blob_name,
)
from quantum.infrastructure.observability.logging.sinks.filesystem.writers.quarantine_writer import (
    QuarantineWriter,
)
from quantum.infrastructure.observability.logging.sinks.filesystem.writers.safe_file_writer import (
    SafeFileWriter,
)

_AUDIT_DISK_ERRORS: Final = define_counter("audit_disk_errors")
_AUDIT_EVENTS_WRITTEN: Final = define_counter("audit_events_written")


class AuditQuarantinePathResolver:
    """
    Determines the quarantine file path for audit failures.
    One file per day, deterministic, minimal, safety-grade.
    """

    def __init__(self, base_dir: Path, env: str, namespace: str, app: str) -> None:
        self._base = base_dir
        self._env = env
        self._ns = namespace
        self._app = app

    def resolve(self, dt: datetime | None = None) -> Path:
        dt = dt or datetime.now(UTC)
        yyyy = dt.strftime("%Y")
        mm = dt.strftime("%m")
        dd = dt.strftime("%d")

        # Name: quarantine-YYYYMMDD.jsonl
        filename = f"quarantine-{yyyy}{mm}{dd}.jsonl"

        path = self._base / self._env / self._ns / self._app / "quarantine" / filename

        path.parent.mkdir(parents=True, exist_ok=True)
        return path


class AuditEventFileHandler(logging.Handler):
    """
    Thread-safe, safety-grade audit event handler.

    Guarantees:
    - 1 event = 1 file (atomic write)
    - NEVER raise
    - Dedicated quarantine channel with guaranteed durability
    """

    def __init__(
        self,
        *,
        base_dir: Path,
        env: str,
        namespace: str,
        app: str,
        encoding: str = "utf-8",
        fsync: bool = True,
    ) -> None:
        super().__init__()
        self._encoding = encoding
        self._fsync = fsync

        # Normal path resolver (1 event = 1 file)
        self._target_base = base_dir / env / namespace / app

        # Quarantine path resolver (1 file per day)
        self._quarantine_resolver = AuditQuarantinePathResolver(
            base_dir=base_dir, env=env, namespace=namespace, app=app
        )

        self._writer = SafeFileWriter(encoding=encoding, fsync=fsync)
        self._quarantine = QuarantineWriter(encoding=encoding, fsync=fsync)

        self._diag = get_diagnostic_logger()
        self._lock = threading.Lock()

        try:
            qpath = self._quarantine_resolver.resolve()
            self._quarantine.open(qpath)
        except Exception:
            # Extremely degraded mode: quarantine itself failed
            self._diag.error("[audit] failed to open quarantine file", exc_info=True)

    # --- Internal Helpers -----------------------------------------------------
    def _write_quarantine(
        self, record: logging.LogRecord, raw_payload: str, reason: str
    ) -> None:
        try:
            self._quarantine.write_error(
                {
                    "error": reason,
                    "logger": record.name,
                    "level": record.levelname,
                    "created": record.created,
                    "raw": raw_payload,
                }
            )
        except Exception:
            # final fallback: never raise
            self.handleError(record)

    # --- Core logic -----------------------------------------------------------
    def emit(self, record: logging.LogRecord) -> None:
        event = getattr(record, "event", None)
        if not isinstance(event, dict):
            return

        with self._lock:
            # JSON serialization (forensic raw)
            try:
                payload = json.dumps(
                    event,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    allow_nan=False,
                )
            except Exception:
                _AUDIT_DISK_ERRORS.inc()
                self._write_quarantine(
                    record, "<unserializable>", "audit_serialization_failed"
                )
                return

            # Resolve atomic file path
            dt = datetime.fromtimestamp(record.created, tz=UTC)
            blob_name = generate_audit_blob_name(now=dt)
            target_path = self._target_base / blob_name
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Atomic write
            try:
                self._writer.open_atomic(target_path)

                try:
                    self._writer.write_line_raw(payload)
                finally:
                    # ALWAYS close to avoid tmp file leaks
                    with suppress(Exception):
                        self._writer.close()

                _AUDIT_EVENTS_WRITTEN.inc()
            except Exception:
                _AUDIT_DISK_ERRORS.inc()
                self._diag.error(
                    f"[audit] write failed for {target_path}", exc_info=True
                )
                self._write_quarantine(record, payload, "audit_atomic_write_failed")

    # --- Lifecycle --------------------------------------------------------
    def close(self) -> None:
        with self._lock:
            try:
                self._writer.close()
            except Exception:
                self._diag.debug(
                    "AuditEventFileHandler: suppressed error during writer.close()",
                    exc_info=True,
                )

            try:
                self._quarantine.close()
            except Exception:
                self._diag.debug(
                    "AuditEventFileHandler: suppressed error during quarantine.close()",
                    exc_info=True,
                )

        super().close()
