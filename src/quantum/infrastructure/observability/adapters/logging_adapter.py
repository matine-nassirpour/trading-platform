from __future__ import annotations

import logging
import os
from collections.abc import Sequence
from pathlib import Path

from quantum.application.ports.outbound.logging_port import LoggingPort
from quantum.infrastructure.observability.logging.event_emitter import emit_event


class LoggingAdapter(LoggingPort):
    """Concrete implementation of LoggingPort using Quantum's observability stack."""

    def __init__(self) -> None:
        self._logger = logging.getLogger("quantum.logging.adapter")

    # --------------------------------------------------------------------------
    # Log tailing (file read)
    # --------------------------------------------------------------------------
    def tail_jsonl(
        self,
        base_dir: Path,
        pattern: str,
        *,
        chunk_bytes: int,
        max_files: int,
    ) -> Sequence[str]:
        """
        Return recent log lines from JSONL files.
        Robust to partial lines and file rotations.
        """
        try:
            files = sorted(
                base_dir.rglob(pattern),
                key=lambda p: p.stat().st_mtime if p.exists() else 0.0,
                reverse=True,
            )
        except (OSError, FileNotFoundError):
            return []

        lines: list[str] = []
        for fp in files[:max_files]:
            lines.extend(self._read_tail(fp, chunk_bytes))
        return lines

    @staticmethod
    def _read_tail(path: Path, chunk_bytes: int, encoding: str = "utf-8") -> list[str]:
        """Read the last `chunk_bytes` of a file, keeping only complete lines."""
        try:
            with open(path, "rb") as fh:
                fh.seek(0, os.SEEK_END)
                file_end = fh.tell()
                start_offset = max(0, file_end - chunk_bytes)
                fh.seek(start_offset)
                buf = fh.read().decode(encoding, "replace")

            if start_offset > 0:
                buf = buf.split("\n", 1)[-1]  # drop truncated first line

            buf = buf.replace("\r\n", "\n")
            raw_lines = buf.split("\n")
            if raw_lines and buf and not buf.endswith("\n"):
                raw_lines = raw_lines[:-1]
            return [line for line in raw_lines if line.strip()]
        except (OSError, UnicodeDecodeError):
            return []

    # --------------------------------------------------------------------------
    # Structured logging API
    # --------------------------------------------------------------------------
    def emit_info(self, message: str, **attrs) -> None:
        """
        Emit an INFO-level structured log message deterministically,
        with proper redaction via each handler’s formatter chain.
        """
        try:
            record = logging.LogRecord(
                name="quantum.logging.adapter",
                level=logging.INFO,
                pathname=__file__,
                lineno=0,
                msg=message,
                args=(),
                exc_info=None,
                func=None,
            )
            record.attrs = attrs

            root_logger = logging.getLogger()
            for h in root_logger.handlers:
                try:
                    h.acquire()

                    # Apply each handler's filter chain manually
                    for flt in getattr(h, "filters", []):
                        if not flt.filter(record):
                            break

                    # Apply formatter if present (for redaction, schema)
                    fmt = getattr(h, "formatter", None)
                    if fmt:
                        try:
                            fmt.format(record)  # triggers formatter/redactor logic
                        except Exception:
                            pass

                    # Emit directly to handler (thread-safe, deterministic)
                    h.emit(record)
                    if hasattr(h, "flush"):
                        h.flush()
                finally:
                    h.release()

        except Exception as exc:
            logging.getLogger(__name__).warning("emit_info failed: %s", exc)

    def emit_event(self, payload: dict) -> None:
        """Emit an audit/telemetry event via the event emitter."""
        try:
            emit_event(payload)
        except Exception as exc:
            self._logger.warning("Failed to emit event: %s", exc)
