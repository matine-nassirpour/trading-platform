from pathlib import Path
from typing import TypedDict

NumberLike = float | int | str | bytes


class Workspace(TypedDict):
    root: Path
    logs: Path
    audit: Path
