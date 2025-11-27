from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class ExecutablePathConfig(BaseModel):
    """
    Safety-grade value object representing a validated executable path.

    Guarantees:
        • Absolute path only
        • Must exist on disk
        • Must be a file (not a directory)
        • Must be executable (POSIX) or readable (.exe on Windows)
        • Immutable
        • No side effects (pure validation)
        • Clean Architecture compliant
    """

    path: Path = Field(..., description="Absolute path to executable file")

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        arbitrary_types_allowed=False,
    )

    def __init__(self, **data: object) -> None:
        raw_path = data.get("path")

        if raw_path is None:
            raise ValueError("ExecutablePathConfig requires a 'path'")

        p = Path(str(raw_path)).expanduser().resolve()

        # Must be absolute
        if not p.is_absolute():
            raise ValueError(f"Executable path must be absolute: '{p}'")

        # Must exist
        if not p.exists():
            raise ValueError(f"Executable does not exist: '{p}'")

        # Must be a file
        if not p.is_file():
            raise ValueError(f"Path exists but is not a file: '{p}'")

        # Executable check
        if not _is_executable(p):
            raise ValueError(f"Path is not an executable: '{p}'")

        data["path"] = p
        super().__init__(**data)

    def as_path(self) -> Path:
        return self.path

    def __str__(self) -> str:
        return str(self.path)


def _is_executable(path: Path) -> bool:
    """
    Cross-platform executable check:
        • POSIX: path.stat().st_mode & executable bits
        • Windows: checking extension (.exe / .bat / .cmd)
    """
    if path.is_symlink():
        path = path.resolve()

    if hasattr(path, "stat"):

        # POSIX executable bit
        try:
            mode = path.stat().st_mode
            if mode & 0o111:
                return True
        except Exception:
            pass

    # Windows: assume .exe/.bat/.cmd as executables
    suffix = path.suffix.lower()
    if suffix in {".exe", ".bat", ".cmd"}:
        return True

    return False
