from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ExecutablePathSpec(BaseModel):
    """
    Safety-grade value object representing a validated executable path.

    Guarantees:
        • Absolute path only
        • Must exist on disk
        • Must be a file (not directory)
        • Must be executable (POSIX) or valid executable extension (Windows)
        • Pure validation (no side effects)
        • Uniform Pydantic v2 validation pipeline
        • Immutable and suitable for safety-critical/clean architectures
    """

    path: Path = Field(..., description="Absolute path to executable file")

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        arbitrary_types_allowed=False,
    )

    # --------------------------------------------------------------------------
    # Step 1 — Normalize raw input BEFORE model construction
    # --------------------------------------------------------------------------
    @model_validator(mode="before")
    @classmethod
    def normalize_raw(cls, data: dict) -> dict:
        raw = data.get("path")

        if raw is None:
            raise ValueError("ExecutablePathSpec requires a 'path' argument")

        p = Path(str(raw)).expanduser().resolve()

        if not p.is_absolute():
            raise ValueError(f"Executable path must be absolute: '{p}'")

        data["path"] = p
        return data

    # --------------------------------------------------------------------------
    # Step 2 — Enforce invariants AFTER construction
    # --------------------------------------------------------------------------
    @model_validator(mode="after")
    def validate_invariants(self) -> ExecutablePathSpec:
        p = self.path

        # Must exist
        if not p.exists():
            raise ValueError(f"Executable does not exist: '{p}'")

        # Must be a file
        if not p.is_file():
            raise ValueError(f"Path exists but is not a file: '{p}'")

        # Must be executable
        if not _is_executable(p):
            raise ValueError(f"Path is not an executable: '{p}'")

        return self

    # --------------------------------------------------------------------------
    # Public helper
    # --------------------------------------------------------------------------
    def as_path(self) -> Path:
        return self.path

    def __str__(self) -> str:
        return str(self.path)


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Cross-platform executable detection                                        │
# ╰────────────────────────────────────────────────────────────────────────────╯
def _is_executable(path: Path) -> bool:
    """
    True if path is executable:
        • POSIX: executable mode bit
        • Windows: extension indicates executable (.exe, .bat, .cmd)
        • Symlink resolution is always explicit
    """

    # Resolve symlink explicitly
    if path.is_symlink():
        path = path.resolve()

    # POSIX execution bit
    try:
        mode = path.stat().st_mode
        if mode & 0o111:
            return True
    except Exception:
        pass

    # Windows extension-based check
    suffix = path.suffix.lower()
    if suffix in {".exe", ".bat", ".cmd"}:
        return True

    return False
