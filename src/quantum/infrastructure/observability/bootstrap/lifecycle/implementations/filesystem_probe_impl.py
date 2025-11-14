from __future__ import annotations

import os

from contextlib import suppress
from pathlib import Path

from quantum.infrastructure.observability.bootstrap.lifecycle.configs.filesystem_probe_config import (
    FileSystemProbeConfig,
)
from quantum.infrastructure.observability.bootstrap.lifecycle.protocols.filesystem_probe import (
    FileSystemProbe,
)


class FileSystemProbeImpl(FileSystemProbe):
    """
    Default file-system health probe.

    Performs:
      • directory existence + creation
      • basic write-test
      • optional deep probing inside nested partition-like paths
    """

    def is_writable(self, base_dir: Path, config: FileSystemProbeConfig) -> bool:
        try:
            base_dir.mkdir(parents=True, exist_ok=True)

            if not os.access(base_dir, os.W_OK):
                return False

            if config.deep_probe_enabled:
                probe_root = base_dir / "__probe__/yyyy/mm/dd/hh"
                probe_root.mkdir(parents=True, exist_ok=True)

                file_path = probe_root / "probe.jsonl"
                with open(file_path, "w", encoding="utf-8") as fp:
                    fp.write("{}\n")

                file_path.unlink(missing_ok=True)

                with suppress(OSError):
                    probe_root.rmdir()

            return True

        except Exception:
            return False
