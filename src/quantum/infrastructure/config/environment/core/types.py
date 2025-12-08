from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class EnvResolutionResult:
    """
    Pure result of environment resolution (no disk read, no parsing).

    Guarantees:
        • base_dir is a valid directory path
        • env_file is either a valid file Path or None
        • Contains zero actual environment data
        • Fully deterministic and hashable
    """

    base_dir: Path
    env_file: Path | None
