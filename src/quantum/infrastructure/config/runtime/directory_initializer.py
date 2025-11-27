from __future__ import annotations

from pathlib import Path

from quantum.infrastructure.config.value_objects.directory_path import DirectoryPathSpec


def ensure_directory_exists(spec: DirectoryPathSpec) -> Path:
    """
    Infrastructure service responsible for safely ensuring a directory exists.

    This function:
        • performs the side effect explicitly (mkdir -p)
        • isolates impurity from value objects
        • is easy to mock in tests
        • is concurrency-safe via exist_ok=True
        • fits perfectly into Clean Architecture layering
    """
    p = spec.as_path()

    try:
        p.mkdir(parents=True, exist_ok=True)
    except Exception as exc:  # nosec B110
        raise RuntimeError(f"Failed to create directory '{p}': {exc}") from exc

    if not p.exists() or not p.is_dir():
        raise RuntimeError(f"'{p}' is not a directory after creation attempt.")

    return p
