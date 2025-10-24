from __future__ import annotations

import os
from pathlib import Path


def inc_disk_error_counter() -> None:
    """
    Increments a Prometheus metric if it exists, otherwise no-op.
    Avoids a hard dependency on metrics.health.
    """
    try:
        from quantum.infrastructure.observability.metrics.collectors.health_collector import (
            logging_disk_errors_total,
        )

        logging_disk_errors_total.inc()
    except (ImportError, AttributeError, NameError):
        pass


def fsync_dir(path: Path) -> None:
    """
    Performs a fsync of the parent directory (POSIX).
    """
    try:
        o_directory = getattr(os, "O_DIRECTORY", None)
        if o_directory is None:  # Windows / FS without O_DIRECTORY
            return
        flags = getattr(os, "O_RDONLY", 0) | o_directory
        dir_fd = os.open(str(path), flags)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except (OSError, AttributeError):
        pass


def safe_unlink(path: Path) -> None:
    """
    Deletes a file in best-effort, silent on error.
    """
    try:
        if path is not None:
            path.unlink(missing_ok=True)  # type: ignore[arg-type]
    except OSError:
        pass
