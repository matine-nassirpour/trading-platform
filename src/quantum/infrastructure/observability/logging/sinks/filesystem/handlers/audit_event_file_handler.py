import json
import logging
import threading

from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from quantum.infrastructure.observability.logging.runtime.diagnostics import (
    get_diagnostic_logger,
)
from quantum.infrastructure.observability.logging.runtime.metrics import define_counter
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
_AUDIT_WRITES: Final = define_counter("audit_events_written")


class AuditFilePathResolver:
    """
    Pure utility responsible for constructing the target audit file path
    based on the event timestamp, and ensuring the directory structure exists.
    SRP: Naming + directory creation only.
    """

    def __init__(self, base_dir: Path, env: str, namespace: str, app: str) -> None:
        self._base = base_dir
        self._env = env
        self._ns = namespace
        self._app = app

    def resolve(self, dt: datetime) -> Path:
        """
        Build a new file path for an audit event at timestamp dt.
        """
        blob_name = generate_audit_blob_name(now=dt)
        path = self._base / self._env / self._ns / self._app / blob_name
        path.parent.mkdir(parents=True, exist_ok=True)
        return path


class AuditEventFileHandler(logging.Handler):
    """
    Thread-safe, safety-grade audit event handler.

    Responsibilities:
    - Serialize a single audit event per file (1 event = 1 JSON file).
    - Atomic write (via SafeFileWriter).
    - Quarantine fallback on malformed payloads or serialization failures.
    - Thread-safe emit() via lock.
    - Deterministic file naming via AuditFilePathResolver.
    """

    def __init__(
        self,
        *,
        base_dir: str,
        env: str,
        namespace: str,
        app: str,
        encoding: str = "utf-8",
        fsync: bool = True,
    ) -> None:
        super().__init__()
        self._encoding = encoding
        self._fsync = fsync

        self._resolver = AuditFilePathResolver(
            base_dir=Path(base_dir),
            env=env,
            namespace=namespace,
            app=app,
        )

        self._writer = SafeFileWriter(encoding=encoding, fsync=fsync)
        self._quarantine = QuarantineWriter(encoding=encoding, fsync=fsync)

        self._lock = threading.Lock()
        self._diag = get_diagnostic_logger()

    # --------------------------------------------------------------------------
    # Internal Helpers
    # --------------------------------------------------------------------------
    def _safe_quarantine(self, record: logging.LogRecord, raw_payload: str) -> None:
        try:
            self._quarantine.write_error(
                {
                    "error": "audit_write_failed",
                    "logger": record.name,
                    "level": record.levelname,
                    "created": record.created,
                    "raw": raw_payload,
                }
            )
        except Exception:
            # final fallback: handlerError never throws
            self.handleError(record)

    # --------------------------------------------------------------------------
    # Core logic
    # --------------------------------------------------------------------------
    def emit(self, record: logging.LogRecord) -> None:
        """
        Thread-safe emit:
        - Extract event dict
        - Resolve target file path
        - Atomic write with SafeFileWriter
        - Quarantine on failures
        """
        event = getattr(record, "event", None)
        if not isinstance(event, dict):
            return  # ignore non-audit records

        dt = datetime.fromtimestamp(record.created, tz=UTC)
        target_path = self._resolver.resolve(dt)

        with self._lock:
            try:
                payload = json.dumps(
                    event, ensure_ascii=False, separators=(",", ":"), allow_nan=False
                )
            except Exception as exc:
                _AUDIT_DISK_ERRORS.inc()
                self._quarantine.write_error(
                    {
                        "error": "audit_serialization_failed",
                        "reason": str(exc),
                        "event": "<unserializable>",
                    }
                )
                return

            try:
                self._writer.open_atomic(target_path)
                self._writer.write_line_raw(payload)
                self._writer.close()
                _AUDIT_WRITES.inc()

            except Exception as exc:
                _AUDIT_DISK_ERRORS.inc()
                self._diag.error(
                    f"[audit] write failed for {target_path}: {exc.__class__.__name__}"
                )
                self._safe_quarantine(record, payload)

    # ----------------------------------------------------------------------
    # Lifecycle
    # ----------------------------------------------------------------------
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
