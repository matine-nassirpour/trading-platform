from __future__ import annotations

import functools
import os

from pathlib import Path
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, model_validator

# Allowed Windows executable extensions
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
    b"\x7fELF",  # Linux ELF
    b"\xfe\xed\xfa\xce",
    b"\xcf\xfa\xed\xfe",
    b"\xce\xfa\xed\xfe",  # macOS Mach-O
    b"MZ",  # Windows PE
)


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Internal Helpers                                                           │
# ╰────────────────────────────────────────────────────────────────────────────╯
def _validate_magic_bytes(path: Path) -> bool:
    """
    Validate executable signature using magic bytes.

    • Reads first 4–8 bytes (zero risk)
    • No silent failures
    • Cross-platform heuristic
    """
    try:
        with path.open("rb") as f:
            header = f.read(8)
    except Exception as e:
        raise ValueError(
            f"Failed to read file header for executable validation: {path}"
        ) from e

    return any(header.startswith(prefix) for prefix in _MAGIC_PREFIXES)


def _is_executable_posix(path: Path) -> bool:
    """POSIX executable bit check with explicit error handling."""
    try:
        mode = path.stat().st_mode
    except Exception as e:
        raise ValueError(f"Unable to stat file for executable check: {path}") from e

    return bool(mode & 0o111)


def _is_executable_windows(path: Path) -> bool:
    """Windows extension-based check."""
    return path.suffix.lower() in _WINDOWS_EXECUTABLE_EXT


@functools.lru_cache(maxsize=256)
def _is_executable(path: Path, *, require_magic: bool) -> bool:
    """
    Unified executable detection (POSIX + Windows + Magic bytes).

    Caching ensures fast repeated validation in quant systems.

    require_magic:
        • If True  → requires a valid executable signature (ELF/Mach-O/PE)
        • If False → extension/permission-based detection is sufficient
    """

    # Windows
    if os.name == "nt":
        if not _is_executable_windows(path):
            return False
        return True if not require_magic else _validate_magic_bytes(path)

    # POSIX
    if not _is_executable_posix(path):
        return False

    return True if not require_magic else _validate_magic_bytes(path)


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
        • Optional magic-bytes validation for executable authenticity
        • Cross-platform robustness
        • Zero side effects
        • Immutable (frozen)
        • Suitable for Clean Architecture, secure operations, and safety-critical use
    """

    path: Path = Field(..., description="Absolute path to an executable file")

    allow_symlink: bool = Field(
        default=False,
        description="Allow executable to be a symlink (default False for safety-critical systems).",
    )

    require_magic: bool = Field(
        default=True,
        description="Validate actual executable signature (ELF/Mach-O/PE). Recommended=True for all production-grade systems.",
    )

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        arbitrary_types_allowed=False,
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
        except Exception as e:
            raise ValueError(f"Invalid path value: {raw!r}") from e

        try:
            # strict=False: preserves non-existent parent resolution
            p = p.resolve(strict=False)
        except Exception as e:
            raise ValueError(f"Failed to resolve path '{raw}': {e}") from e

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

        # ─── Symlink policy
        if p.is_symlink() and not self.allow_symlink:
            raise ValueError(
                f"Executable symlink is not permitted: '{p}' " "(allow_symlink=False)"
            )

        # ─── File existence
        if not p.exists():
            raise ValueError(f"Executable does not exist: '{p}'")

        if not p.is_file():
            raise ValueError(f"Executable path is not a file: '{p}'")

        # ─── Executable detection
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
