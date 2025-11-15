from __future__ import annotations

import os

from pathlib import Path

from quantum.infrastructure.observability.logging.core.diagnostics import (
    get_diagnostic_logger,
)


def fsync_dir(path: Path) -> None:
    """
    POSIX directory fsync with diagnostic fallback.
    """
    try:
        o_directory = getattr(os, "O_DIRECTORY", None)
        if o_directory is None:
            return

        flags = getattr(os, "O_RDONLY", 0) | o_directory
        dir_fd = os.open(str(path), flags)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)

    except Exception as exc:
        get_diagnostic_logger().error(
            f"fsync_dir failed for path={path!s}: {exc.__class__.__name__}"
        )


def safe_unlink(path: Path) -> None:
    """
    Delete a file safely with diagnostic logging.
    """
    try:
        if path is not None:
            path.unlink(missing_ok=True)
    except Exception as exc:
        get_diagnostic_logger().error(
            f"safe_unlink failed for path={path!s}: {exc.__class__.__name__}"
        )
