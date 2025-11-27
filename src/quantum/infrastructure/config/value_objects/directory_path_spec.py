from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DirectoryPathSpec(BaseModel):
    """
    Pure, safety-grade value object representing a validated directory path spec.

    Guarantees:
        • Absolute path required
        • Must represent a directory path (may or may not exist)
        • No side effects (no creation)
        • Immutable
        • Pydantic v2 canonical validation via model_validator
        • Suitable for Clean Architecture and safety-critical systems
    """

    path: Path = Field(..., description="Absolute directory path (pure spec).")

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        arbitrary_types_allowed=False,
    )

    # --------------------------------------------------------------------------
    # Validation
    # --------------------------------------------------------------------------
    @model_validator(mode="before")
    @classmethod
    def validate_raw(cls, data: dict) -> dict:
        """
        Normalize and enforce invariants before model construction.
        """
        raw = data.get("path")
        if raw is None:
            raise ValueError("DirectoryPathSpec requires a 'path' argument.")

        p = Path(str(raw)).expanduser().resolve()

        # Absolute path only
        if not p.is_absolute():
            raise ValueError(f"Directory path must be absolute: '{p}'")

        # Security: must not refer to an existing file
        if p.exists() and not p.is_dir():
            raise ValueError(f"Path exists but is not a directory: '{p}'")

        data["path"] = p
        return data

    # --------------------------------------------------------------------------
    # API Methods
    # --------------------------------------------------------------------------
    def as_path(self) -> Path:
        """Return the underlying Path."""
        return self.path

    def __str__(self) -> str:
        return str(self.path)
