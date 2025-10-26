from __future__ import annotations

import os
from pathlib import Path


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Metrics Integration                                                        │
# ╰────────────────────────────────────────────────────────────────────────────╯
def inc_disk_error_counter() -> None:
    """
    Increment the Prometheus counter for disk I/O errors, if available.

    This function performs a best-effort import of the observability
    metrics collector, but never fails if the collector is absent.
    """
    try:
        from quantum.infrastructure.observability.metrics.collectors.health_collector import (
            logging_disk_errors_total,
        )

        logging_disk_errors_total.inc()
    except (ImportError, AttributeError, NameError):
        # Metrics module unavailable — silently degrade
        pass


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ POSIX Directory Sync                                                       │
# ╰────────────────────────────────────────────────────────────────────────────╯
def fsync_dir(path: Path) -> None:
    """
    Perform a POSIX `fsync` on a directory to guarantee the durability
    of metadata updates (e.g. after atomic file renames).

    On non-POSIX systems or when `os.O_DIRECTORY` is not available,
    this operation is silently skipped.
    """
    try:
        o_directory: int | None = getattr(os, "O_DIRECTORY", None)
        if o_directory is None:
            return  # non-POSIX (e.g., Windows)
        flags: int = getattr(os, "O_RDONLY", 0) | o_directory
        dir_fd: int = os.open(str(path), flags)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except (OSError, AttributeError):
        # Directory might not be syncable — ignore silently
        pass


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Safe File Deletion                                                         │
# ╰────────────────────────────────────────────────────────────────────────────╯
def safe_unlink(path: Path) -> None:
    """
    Delete a file safely, suppressing any exception.

    Args:
        path: Target file path. May be `None` or non-existent.

    This is typically used to remove temporary files after atomic
    writes, ensuring best-effort cleanup without impacting stability.
    """
    try:
        if path is not None:
            path.unlink(missing_ok=True)
    except OSError:
        # File already gone or permission denied — ignore silently
        pass
