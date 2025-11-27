from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class DirectoryPathConfig(BaseModel):
    """
    Safety-grade value object representing a validated directory path.

    Guarantees:
        - Absolute path only
        - Not a file, not a symlink to a file
        - Optionally ensures existence (create=True)
        - Portable across Linux / Windows
        - Immutable (frozen)
        - Clean Architecture compliant (pure value object)

    Notes:
        - This is INFRASTRUCTURE layer: no business rules here.
        - It encapsulates strict filesystem invariants suitable for audit/log directories.
    """

    path: Path = Field(..., description="Absolute and validated directory path")
    create: bool = Field(
        default=False,
        description="If True, directory will be created (mkdir -p) during validation.",
    )

    model_config = ConfigDict(
        frozen=True, extra="forbid", arbitrary_types_allowed=False
    )

    # --------------------------------------------------------------------------
    # Validators
    # --------------------------------------------------------------------------
    def __init__(self, **data: object) -> None:
        raw_path = data.get("path")

        if raw_path is None:
            raise ValueError("DirectoryPathConfig requires a 'path'")

        # Normalize to Path object
        p = Path(str(raw_path)).expanduser().resolve()

        # Absolute path only
        if not p.is_absolute():
            raise ValueError(f"Directory path must be absolute: '{p}'")

        # Security: prevent file paths
        if p.exists() and not p.is_dir():
            raise ValueError(f"Path exists but is not a directory: '{p}'")

        # Optional creation
        if data.get("create", False):
            try:
                p.mkdir(parents=True, exist_ok=True)
            except Exception as exc:  # nosec B110
                raise ValueError(f"Failed to create directory '{p}': {exc}") from exc

        # After creation, must be a directory or non-existing but valid
        if p.exists() and not p.is_dir():
            raise ValueError(f"'{p}' is not a directory after creation attempt.")

        # Mutate the validated path back into data
        data["path"] = p

        super().__init__(**data)

    # --------------------------------------------------------------------------
    # API Methods
    # --------------------------------------------------------------------------
    def as_path(self) -> Path:
        """Return the underlying Path."""
        return self.path

    def __str__(self) -> str:
        return str(self.path)
