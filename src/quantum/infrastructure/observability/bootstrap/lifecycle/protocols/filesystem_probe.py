from __future__ import annotations

from pathlib import Path
from typing import Protocol

from quantum.infrastructure.observability.bootstrap.lifecycle.configs.filesystem_probe_config import (
    FileSystemProbeConfig,
)


class FileSystemProbe(Protocol):
    """
    Protocol for probing filesystem health of persistent logging sinks.

    This interface abstracts:
      • directory creation
      • write tests
      • deep probing strategies
    """

    def is_writable(self, base_dir: Path, config: FileSystemProbeConfig) -> bool:
        """
        Return True if the directory is writable and healthy.
        """
        ...
