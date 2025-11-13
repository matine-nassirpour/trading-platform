import os

from collections.abc import Sequence
from pathlib import Path


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Log tailing (file read)                                                    │
# ╰────────────────────────────────────────────────────────────────────────────╯
def tail_jsonl(
    base_dir: Path,
    pattern: str,
    *,
    chunk_bytes: int,
    max_files: int,
) -> Sequence[str]:
    """
    Return recent log lines from JSONL files.
    Robust to partial lines and file rotations.
    """
    try:
        files = sorted(
            base_dir.rglob(pattern),
            key=lambda p: p.stat().st_mtime if p.exists() else 0.0,
            reverse=True,
        )
    except (OSError, FileNotFoundError):
        return []

    lines: list[str] = []
    for fp in files[:max_files]:
        lines.extend(_read_tail(fp, chunk_bytes))
    return lines


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Helper                                                                     │
# ╰────────────────────────────────────────────────────────────────────────────╯
def _read_tail(path: Path, chunk_bytes: int, encoding: str = "utf-8") -> list[str]:
    """Read the last `chunk_bytes` of a file, keeping only complete lines."""
    try:
        with open(path, "rb") as fh:
            fh.seek(0, os.SEEK_END)
            file_end = fh.tell()
            start_offset = max(0, file_end - chunk_bytes)
            fh.seek(start_offset)
            buf = fh.read().decode(encoding, "replace")

        if start_offset > 0:
            buf = buf.split("\n", 1)[-1]  # drop truncated first line

        buf = buf.replace("\r\n", "\n")
        raw_lines = buf.split("\n")
        if raw_lines and buf and not buf.endswith("\n"):
            raw_lines = raw_lines[:-1]
        return [line for line in raw_lines if line.strip()]
    except (OSError, UnicodeDecodeError):
        return []
