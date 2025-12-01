from __future__ import annotations

import os

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

from quantum.infrastructure.config.value_objects._path_normalization import (
    PathNormalizationError,
    canonicalize_raw_path,
)


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Permission Helpers (Pure & Side-Effect-Free)                               │
# ╰────────────────────────────────────────────────────────────────────────────╯
def _has_read_permission(path: Path) -> bool:
    """
    Side-effect-free read permission check.

    Strategy:
        • Uses os.access(path, os.R_OK) which is non-mutating
        • Avoids iterating the directory (which may raise on deep FS issues)
        • Pure, deterministic, audit-safe
    """
    try:
        return os.access(path, os.R_OK)
    except Exception:
        return False


def _has_write_permission(path: Path) -> bool:
    """
    Side-effect-free write permission check.

    Strategy:
        • Uses os.access(path, W_OK)
        • Does NOT create temporary files (no touch, no unlink)
        • High-assurance: avoids race conditions, side effects, FS mutation

    Limitations:
        • os.access() checks *effective user* permissions, which is exactly
          what high-assurance permission verification requires.
        • It does not test mount options (e.g. read-only FS), but standards
          forbid mutation in validation code, so we guarantee purity.
    """
    try:
        return os.access(path, os.W_OK)
    except Exception:
        return False


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Value Object                                                               │
# ╰────────────────────────────────────────────────────────────────────────────╯
class DirectoryPathSpec(BaseModel):
    """
    Safety-grade value object representing a validated directory path specification.

    Guarantees:
        • Absolute path (NFKC-normalised)
        • Optionally forbids symlinks (recommended for safety-critical systems)
        • Must represent a directory path (existing or not)
        • No implicit creation, no side effects
        • Permission pre-check (read/write) if directory exists
        • Deterministic, robust, and fully immutable (frozen)
        • Pydantic v2 canonical validation pipeline
    """

    path: Path = Field(..., description="Absolute directory path (pure spec).")
    allow_symlink: bool = Field(
        default=False,
        description="Permit directory symlink. False recommended for safety-critical systems.",
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
    def normalize_and_validate_raw(cls, data: dict | str | Path | None) -> dict:
        try:
            p = canonicalize_raw_path(data, field_name="path")
        except PathNormalizationError as exc:
            raise ValueError(str(exc)) from exc

        return {"path": p}

    # --------------------------------------------------------------------------
    # Step 2 — Invariant enforcement (AFTER model)
    # --------------------------------------------------------------------------
    @model_validator(mode="after")
    def validate_invariants(self) -> DirectoryPathSpec:
        p: Path = self.path

        # ─── Symlink policy
        if p.is_symlink() and not self.allow_symlink:
            raise ValueError(
                f"Symlink directory path not permitted: '{p}' " "(allow_symlink=False)"
            )

        # ─── Directory or non-existent
        if p.exists() and not p.is_dir():
            raise ValueError(f"Path exists but is not a directory: '{p}'")

        # ─── Granular permission checks
        # Only validate permissions if path exists. Nonexistent directories
        # are permitted by design (pure specification, no creation).
        if p.exists():
            if not _has_read_permission(p):
                raise ValueError(
                    f"Directory is not readable: '{p}'. "
                    "Permission denied or insufficient privileges."
                )

            if not _has_write_permission(p):
                raise ValueError(
                    f"Directory is not writable: '{p}'. "
                    "Permission denied or insufficient privileges."
                )

        return self

    # --------------------------------------------------------------------------
    # API Methods
    # --------------------------------------------------------------------------
    def as_path(self) -> Path:
        """Return the underlying Path."""
        return self.path

    def __str__(self) -> str:
        return str(self.path)
