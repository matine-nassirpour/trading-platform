from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class EnvResolutionResult:
    """
    Pure, immutable environment resolution result.

    Preconditions (enforced by callers):
        • base_dir: a valid directory
        • env_file: valid file or None
    """

    base_dir: Path
    env_file: Path | None
