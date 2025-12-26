from __future__ import annotations

import os

from pathlib import Path
from typing import IO

from quantum.infrastructure.observability.logging.sinks.filesystem.fsync_utils import (
    fsync_dir,
)


class SafeFileWriter:
    """
    Safety-grade, low-level file writer with:
    - atomic write via temp file + os.replace()
    - optional fsync durability
    - explicit open/close lifecycle
    - deterministic behavior under failure
    - unified API for audit & partitioned handlers
    """

    def __init__(self, *, encoding: str = "utf-8", fsync: bool = True) -> None:
        self._encoding = encoding
        self._fsync = fsync

        self._fh: IO[str] | None = None
        self._path: Path | None = None
        self._tmp_path: Path | None = None
        self._mode_atomic = False

    # --------------------------------------------------------------------------
    # Properties
    # --------------------------------------------------------------------------
    @property
    def path(self) -> Path | None:
        return self._path

    def size(self) -> int:
        if not self._fh:
            return 0
        return self._fh.tell()

    # --------------------------------------------------------------------------
    # Append mode (partitioned handler)
    # --------------------------------------------------------------------------
    def open_append(self, path: Path) -> None:
        """
        Open the file in append mode (streaming writes).
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        self._mode_atomic = False
        self._path = path
        self._tmp_path = None

        self._fh = open(path, "a", encoding=self._encoding, newline="\n")

        # directory durability
        if self._fsync:
            fsync_dir(path.parent)

    # --------------------------------------------------------------------------
    # Atomic mode (audit handler) open → write → close
    # --------------------------------------------------------------------------
    def open_atomic(self, path: Path) -> None:
        """
        Open a *temporary* file for atomic replace on close().
        """
        # Prepare directories
        path.parent.mkdir(parents=True, exist_ok=True)

        self._mode_atomic = True
        self._path = path
        self._tmp_path = path.with_suffix(path.suffix + ".tmp")

        # Ensure cleanup of stale temp files
        try:
            self._tmp_path.unlink(missing_ok=True)
        except Exception:
            return

        self._fh = open(self._tmp_path, "w", encoding=self._encoding, newline="\n")

    # --------------------------------------------------------------------------
    # Writing
    # --------------------------------------------------------------------------
    def write_line(self, line: str) -> None:
        """Write a line + newline"""
        if self._fh is None:
            raise RuntimeError("SafeFileWriter.write_line() called before open().")

        self._fh.write(line + "\n")

    def write_line_raw(self, line: str) -> None:
        """
        Write raw content *without* adding a newline.
        Used by audit handler which writes full JSON objects.
        """
        if self._fh is None:
            raise RuntimeError("SafeFileWriter.write_line_raw() called before open().")

        self._fh.write(line)

    # --------------------------------------------------------------------------
    # Closing → fsync → atomic replace
    # --------------------------------------------------------------------------
    def _finalize_atomic_replace(self) -> None:
        tmp = self._tmp_path
        final = self._path

        if tmp is None or final is None:
            return  # degraded but safe

        try:
            os.replace(tmp, final)
        except Exception:
            # degraded mode: remove temp file if possible
            try:
                tmp.unlink(missing_ok=True)
            except Exception:
                pass

            # atomicity failure is critical but NEVER raise
            return

        if self._fsync:
            fsync_dir(final.parent)

    def close(self) -> None:
        """
        Flush → fsync → atomic replace(temp, final) → fsync directory.
        """
        if self._fh is None:
            return

        try:
            self._fh.flush()
            if self._fsync:
                try:
                    os.fsync(self._fh.fileno())
                except Exception:
                    pass
            self._fh.close()

            if self._mode_atomic:
                self._finalize_atomic_replace()

        finally:
            self._fh = None
            self._path = None
            self._tmp_path = None
            self._mode_atomic = False
