from __future__ import annotations

import json

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

    def __init__(self, encoding: str = "utf-8") -> None:
        self._encoding = encoding
        self._fh = None
        self._path: Path | None = None

    def open(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = open(path, "a", encoding=self._encoding, newline="\n")
        self._path = path
        fsync_dir(path.parent)

    def write_error(self, record_data: dict[str, Any]) -> None:
        assert self._fh is not None
        line = json.dumps(record_data, ensure_ascii=False, allow_nan=False)
        self._fh.write(line + "\n")
        self._fh.flush()

    def close(self) -> None:
        try:
            if self._fh:
                self._fh.flush()
                self._fh.close()
        finally:
            self._fh = None
            self._path = None
