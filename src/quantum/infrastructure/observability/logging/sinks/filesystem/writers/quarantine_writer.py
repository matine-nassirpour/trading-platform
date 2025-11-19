from __future__ import annotations

import json
import os

from pathlib import Path
from typing import Any

from quantum.infrastructure.observability.logging.sinks.filesystem.fsync_utils import (
    fsync_dir,
)


class QuarantineWriter:
    """
    Safety-critical quarantine logic.
    Dedicated writer to isolate corrupted records.
    """

    def __init__(self, *, encoding: str = "utf-8", fsync: bool = True) -> None:
        self._encoding = encoding
        self._fsync = fsync

        self._fh = None
        self._path: Path | None = None

    def open(self, path: Path) -> None:
        """Open a stream in append mode for quarantine records."""
        path.parent.mkdir(parents=True, exist_ok=True)

        self._fh = open(path, "a", encoding=self._encoding, newline="\n")
        self._path = path

        if self._fsync:
            fsync_dir(path.parent)

    def write_error(self, record_data: dict[str, Any]) -> None:
        """
        Write a forensic record into the quarantine file.
        Guaranteed non-raising (except catastrophic failures).
        """
        if self._fh is None:
            raise RuntimeError("QuarantineWriter.write_error() called before open().")

        line = json.dumps(record_data, ensure_ascii=False, allow_nan=False)
        self._fh.write(line + "\n")
        self._fh.flush()

        if self._fsync:
            try:
                os.fsync(self._fh.fileno())
            except Exception:
                # Do not raise, quarantine must NEVER break a handler
                return

    def close(self) -> None:
        if self._fh is None:
            return

        try:
            try:
                self._fh.flush()
                if self._fsync:
                    try:
                        os.fsync(self._fh.fileno())
                    except Exception:
                        # Closing must never raise in quarantine.
                        # Failure to fsync on close does not affect safety guarantees.
                        return
            finally:
                self._fh.close()
        finally:
            self._fh = None
            self._path = None
