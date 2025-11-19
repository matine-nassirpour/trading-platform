from __future__ import annotations

import os

from pathlib import Path

from quantum.infrastructure.observability.logging.sinks.filesystem.fsync_utils import (
    fsync_dir,
)


class SafeFileWriter:
    """
    Handles low-level durability for events:
    - open/close
    - atomic replace
    - fsync
    - deterministic behavior
    """

    def __init__(self, encoding: str = "utf-8") -> None:
        self._encoding = encoding
        self._fh = None  # type: ignore
        self._path: Path | None = None

    @property
    def path(self) -> Path | None:
        return self._path

    def open(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = open(path, "a", encoding=self._encoding, newline="\n")
        self._path = path
        fsync_dir(path.parent)

    def write_line(self, line: str) -> None:
        assert self._fh is not None
        self._fh.write(line + "\n")
        self._fh.flush()
        os.fsync(self._fh.fileno())

    def size(self) -> int:
        if not self._fh:
            return 0
        return self._fh.tell()

    def close(self) -> None:
        try:
            if self._fh:
                self._fh.flush()
                self._fh.close()
        finally:
            self._fh = None
            self._path = None
