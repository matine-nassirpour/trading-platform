from __future__ import annotations

import unicodedata

from pathlib import Path
from typing import Any


class PathNormalizationError(ValueError):
    """Explicit error type for raw-path normalization failures."""


def _extract_raw_path(data: Any, *, field_name: str) -> Any:
    """
    Extract raw 'path' from all accepted input shapes.

    Accepted:
        • mapping {field_name: "..."}
        • bare string
        • bare Path
        • Anything convertible to str

    NEVER performs any filesystem mutation.
    NEVER resolves symlinks semantically (left to invariants).
    """
    if data is None:
        raise PathNormalizationError(f"'{field_name}' is required but received None.")

    if isinstance(data, dict):
        if field_name not in data:
            raise PathNormalizationError(f"'{field_name}' field missing from mapping.")
        return data[field_name]

    # String / Path / Other → convertible to str later
    return data


def _unicode_normalize(value: str) -> str:
    """
    NFKC normalization ensures:
        • Unicode canonical stability
        • Homoglyph mitigation
        • Safety-critical determinism
    """
    try:
        return unicodedata.normalize("NFKC", value)
    except Exception as exc:
        raise PathNormalizationError(
            f"Failed to NFKC-normalize value: {value!r}"
        ) from exc


def canonicalize_raw_path(
    raw_input: Any,
    *,
    field_name: str = "path",
) -> Path:
    """
    Canonical, safety-grade 'raw → Path' transformation shared by all PathSpec.

    Responsibilities:
        • Extract path from accepted shapes (dict / str / Path)
        • Convert to string
        • Unicode-normalize (NFKC)
        • Expand '~' (expanduser)
        • Resolve with strict=False (canonicalization, no mutation)
        • Enforce absolute path requirement

    NO:
        × Permission checks
        × File/directory existence checks
        × Executability checks
        × Symlink policy enforcement

    These invariants belong to the specific Value Objects.

    Returns:
        A fully canonical, absolute Path.

    Raises:
        PathNormalizationError  (on any failure)
    """
    raw = _extract_raw_path(raw_input, field_name=field_name)

    # Normalize to str with Unicode NFKC normalization
    try:
        s = _unicode_normalize(str(raw))
    except Exception as exc:
        raise PathNormalizationError(f"Invalid raw path value {raw!r}") from exc

    # Convert to Path and expand '~'
    try:
        p = Path(s).expanduser()
    except Exception as exc:
        raise PathNormalizationError(f"Failed to convert {s!r} into Path") from exc

    # Resolve without raising — but canonicalize the path
    try:
        p = p.resolve(strict=False)
    except Exception as exc:
        raise PathNormalizationError(f"Failed to resolve path '{p}': {exc}") from exc

    if not p.is_absolute():
        raise PathNormalizationError(
            f"Path must be absolute after canonicalization: '{p}'"
        )

    return p
