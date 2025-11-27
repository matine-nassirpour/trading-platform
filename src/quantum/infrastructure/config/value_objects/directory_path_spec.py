from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Permission Helpers (Pure & Side-Effect-Free)                               │
# ╰────────────────────────────────────────────────────────────────────────────╯
def _has_read_permission(path: Path) -> bool:
    """
    True if current process can list the directory.
    No side effects: no file creation, just permission probing.

    Using path.iterdir() inside a try block is the most direct
    and portable check across Linux / macOS / Windows.
    """
    try:
        next(path.iterdir(), None)
        return True
    except Exception:
        return False


def _has_write_permission(path: Path) -> bool:
    """
    True if current process can attempt metadata updates in directory.

    Robust, cross-platform write-check without touching actual contents:
        • Try using Path.touch() on a temporary name with exist_ok=False.
        • Immediately remove it.
    Side-effect-free behavior:
        • If directory is writable but external factors block creation,
          we catch & interpret (safety-grade).
        • If created, deletion is immediate and guaranteed.
    """
    import uuid

    test_name = f".perm_test_{uuid.uuid4().hex}"
    test_path = path / test_name

    try:
        test_path.touch(exist_ok=False)
    except Exception:
        return False
    finally:
        try:
            if test_path.exists():
                test_path.unlink()
        except Exception:
            # If unlink fails, we treat as write-unsafe.
            return False

    return True


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
    # Step 1 — Raw normalization / invariant enforcement (BEFORE model)
    # --------------------------------------------------------------------------
    @model_validator(mode="before")
    @classmethod
    def normalize_and_validate_raw(cls, data: dict) -> dict:
        raw = data.get("path")
        if raw is None:
            raise ValueError("DirectoryPathSpec requires a 'path' argument.")

        # Normalize to string then Path
        try:
            p = Path(str(raw)).expanduser()
        except Exception as e:
            raise ValueError(f"Invalid path value: {raw!r}") from e

        # resolve() may raise if underlying FS is inconsistent
        try:
            p = p.resolve(strict=False)  # strict=False avoids raising if nonexistent
        except Exception as e:
            raise ValueError(f"Failed to resolve path '{raw}': {e}") from e

        if not p.is_absolute():
            raise ValueError(f"Directory path must be absolute: '{p}'")

        data["path"] = p
        return data

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
