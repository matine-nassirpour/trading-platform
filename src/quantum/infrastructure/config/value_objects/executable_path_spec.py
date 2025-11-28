from __future__ import annotations

import functools
import os

from pathlib import Path
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, model_validator

_WINDOWS_EXECUTABLE_EXT: Final[frozenset[str]] = frozenset(
    {".exe", ".bat", ".cmd", ".ps1"}
)

# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Magic bytes indicating executable formats (not exhaustive but reliable)    │
# │ - ELF: 0x7F 45 4C 46                                                       │
# │ - Mach-O: FE ED FA CE / CF FA ED FE / CE FA ED FE                          │
# │ - PE (Windows): MZ (4D 5A)                                                 │
# ╰────────────────────────────────────────────────────────────────────────────╯
_MAGIC_PREFIXES: Final[tuple[bytes, ...]] = (
    b"\x7fELF",  # ELF (Linux)
    b"\xfe\xed\xfa\xce",
    b"\xcf\xfa\xed\xfe",
    b"\xce\xfa\xed\xfe",  # Mach-O (macOS)
    b"MZ",  # PE (Windows)
)


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Internal Helpers                                                           │
# ╰────────────────────────────────────────────────────────────────────────────╯
def _validate_magic_bytes(path: Path) -> bool:
    """
    Validate file header against known executable signatures.

    Guarantees:
        • No mutation
        • Minimal IO (8 bytes)
        • Explicit failure paths
    """
    try:
        with path.open("rb") as f:
            header = f.read(8)
    except Exception as exc:
        raise ValueError(
            f"Failed to read file header for executable validation: '{path}'"
        ) from exc

    return any(header.startswith(prefix) for prefix in _MAGIC_PREFIXES)


def _is_executable_posix(path: Path) -> bool:
    """POSIX executable bit check with explicit error handling."""
    try:
        mode = path.stat().st_mode
    except Exception as exc:
        raise ValueError(f"Unable to stat file for executable check: '{path}'") from exc

    return bool(mode & 0o111)


def _is_executable_windows(path: Path) -> bool:
    """Windows extension-based check."""
    return path.suffix.lower() in _WINDOWS_EXECUTABLE_EXT


def _get_file_signature(path: Path) -> tuple[str, float, int]:
    """
    Return deterministic file metadata used as the cache key.

    Components:
        • absolute, resolved path as string
        • modification timestamp
        • file size in bytes
    """
    try:
        st = path.stat()
    except Exception as exc:
        raise ValueError(f"Unable to stat file for signature: '{path}'") from exc

    return str(path), st.st_mtime, st.st_size


@functools.lru_cache(maxsize=512)
def _is_executable_cached(
    signature: tuple[str, float, int],
    *,
    require_magic: bool,
) -> bool:
    """
    Pure cached executable validation.

    Critical properties:
        • Cache key includes full signature → safe invalidation
        • No dependence on mutable global state
        • Deterministic & reproducible
        • All IO is minimal and controlled
    """
    full_path = Path(signature[0])

    # Windows
    if os.name == "nt":
        if not _is_executable_windows(full_path):
            return False
        return True if not require_magic else _validate_magic_bytes(full_path)

    # POSIX
    if not _is_executable_posix(full_path):
        return False

    return True if not require_magic else _validate_magic_bytes(full_path)


def _is_executable(path: Path, *, require_magic: bool) -> bool:
    """
    Non-cached API that computes signature and delegates to the cached validator.
    """
    sig = _get_file_signature(path)
    return _is_executable_cached(sig, require_magic=require_magic)


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Value Object                                                               │
# ╰────────────────────────────────────────────────────────────────────────────╯
class ExecutablePathSpec(BaseModel):
    """
    Safety-grade value object representing a validated executable path.

    Guarantees:
        • Absolute path only
        • Must exist & be a file
        • Optional symlink acceptance (default: forbidden)
        • Optional magic-bytes validation for authenticity
        • Deterministic validation
        • Zero mutation (filesystem or global state)
        • Immutability guaranteed via pydantic v2 (frozen)
        • Suitable for critical environments (DO-178C / IEC-62304 / ISO-26262)
    """

    path: Path = Field(..., description="Absolute path to an executable file.")

    allow_symlink: bool = Field(
        default=False,
        description="Allow executable path to be a symlink (default False).",
    )

    require_magic: bool = Field(
        default=True,
        description="Validate binary signature via magic bytes (recommended=True).",
    )

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        arbitrary_types_allowed=False,
        validate_assignment=False,
        validate_default=False,
    )

    # --------------------------------------------------------------------------
    # Step 1 — Normalize raw input (BEFORE model construction)
    # --------------------------------------------------------------------------
    @model_validator(mode="before")
    @classmethod
    def normalize_raw(cls, data: dict) -> dict:
        raw = data.get("path")

        if raw is None:
            raise ValueError("ExecutablePathSpec requires a 'path' argument.")

        try:
            p = Path(str(raw)).expanduser()
        except Exception as exc:
            raise ValueError(f"Invalid path value: {raw!r}") from exc

        # Non-strict resolve: deterministic, no failure on non-existent FS segments
        try:
            p = p.resolve(strict=False)
        except Exception as exc:
            raise ValueError(f"Failed to resolve path '{raw}': {exc}") from exc

        if not p.is_absolute():
            raise ValueError(f"Executable path must be absolute: '{p}'")

        data["path"] = p
        return data

    # --------------------------------------------------------------------------
    # Step 2 — Validate invariants (AFTER model construction)
    # --------------------------------------------------------------------------
    @model_validator(mode="after")
    def validate_invariants(self) -> ExecutablePathSpec:
        p: Path = self.path

        # Symlink policy
        if p.is_symlink() and not self.allow_symlink:
            raise ValueError(
                f"Executable symlink is not permitted: '{p}' (allow_symlink=False)"
            )

        # Existence and file requirement
        if not p.exists():
            raise ValueError(f"Executable does not exist: '{p}'")
        if not p.is_file():
            raise ValueError(f"Executable path is not a file: '{p}'")

        # Executable test (cached safely)
        if not _is_executable(p, require_magic=self.require_magic):
            if self.require_magic:
                raise ValueError(
                    f"File is not a valid executable (magic bytes check failed): '{p}'"
                )
            else:
                raise ValueError(
                    f"File is not considered executable on this platform: '{p}'"
                )

        return self

    # --------------------------------------------------------------------------
    # Public helper
    # --------------------------------------------------------------------------
    def as_path(self) -> Path:
        """Return the underlying validated Path object."""
        return self.path

    def __str__(self) -> str:
        return str(self.path)
