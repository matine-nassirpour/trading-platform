from __future__ import annotations

import os
from pathlib import Path


def inc_disk_error_counter() -> None:
    """
    Increments a Prometheus metric if it exists, otherwise no-op.
    Avoids a hard dependency on metrics.health.
    """
    try:
        from quantum.infrastructure.observability.metrics.health import (  # type: ignore; noqa: F401
            logging_disk_errors_total,
        )

        logging_disk_errors_total.inc()
    except (ImportError, AttributeError, NameError):
        pass


def fsync_dir(path: Path) -> None:
    """
    Performs a fsync of the parent directory to ensure the rename is durable (os.replace).
    Most POSIX FSs support this. On platforms where O_DIRECTORY doesn't exist,
    or if the FS doesn't allow it, it's silently ignored.
    """
    try:
        dir_fd = os.open(str(path), os.O_DIRECTORY)  # type: ignore[attr-defined]
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except OSError:
        # Best-effort only
        pass


def safe_unlink(path: Path) -> None:
    """
    Deletes a file in best-effort, silent on error.
    """
    try:
        path.unlink(missing_ok=True)  # type: ignore[arg-type]
    except OSError:
        pass
