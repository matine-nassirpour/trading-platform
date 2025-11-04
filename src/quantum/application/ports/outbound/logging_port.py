from collections.abc import Sequence
from pathlib import Path
from typing import Protocol


class LoggingPort(Protocol):
    """Structural interface for log emission and retrieval."""

    def tail_jsonl(
        self,
        base_dir: Path,
        pattern: str,
        *,
        chunk_bytes: int,
        max_files: int,
    ) -> Sequence[str]:
        """Return recent log lines from JSONL files (complete lines only)."""
        ...

    def emit_info(self, message: str, **attrs) -> None:
        """Emit a structured INFO-level log message."""
        ...

    def emit_event(self, payload: dict) -> None:
        """Emit a structured audit event (schema-validated)."""
        ...
