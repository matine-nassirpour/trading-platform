from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from quantum.infrastructure.observability.logging.sinks.filesystem.naming import (
    bad_filename,
    events_filename,
    partition_path_components,
)


@dataclass(frozen=True)
class PartitionDecision:
    dir_path: Path
    events_path: Path
    bad_path: Path
    next_part_index: int
    rollover_required: bool


class PartitionPolicy:
    """
    Pure policy:
    - no I/O
    - no logging
    - no state
    Safety-grade:
    - deterministic
    - reproducible
    """

    def __init__(
        self,
        base_dir: Path,
        env: str,
        namespace: str,
        app: str,
        max_bytes: int,
    ) -> None:
        self._base = base_dir
        self._env = env
        self._ns = namespace
        self._app = app
        self._max = max_bytes

    def decide(
        self,
        *,
        record_timestamp: float,
        part_index: int,
        current_path: Path | None,
        current_size: int,
    ) -> PartitionDecision:
        dt = datetime.fromtimestamp(record_timestamp, tz=UTC)
        yyyy, mm, dd, hh = partition_path_components(dt)

        dir_path = self._base / self._env / self._ns / self._app / yyyy / mm / dd / hh

        # Case 1 — new hour partition
        if current_path is None or current_path.parent != dir_path:
            next_index = 0
            events = dir_path / events_filename(yyyy, mm, dd, hh, 0)
            bad = dir_path / bad_filename(yyyy, mm, dd, hh, 0)
            rollover = True

        # Case 2 — size-based rotation
        elif 0 < self._max <= current_size:
            next_index = part_index + 1
            events = dir_path / events_filename(yyyy, mm, dd, hh, next_index)
            bad = dir_path / bad_filename(yyyy, mm, dd, hh, next_index)
            rollover = True

        # Case 3 — continue in same file
        else:
            next_index = part_index
            events = dir_path / events_filename(yyyy, mm, dd, hh, part_index)
            bad = dir_path / bad_filename(yyyy, mm, dd, hh, part_index)
            rollover = False

        return PartitionDecision(
            dir_path=dir_path,
            events_path=events,
            bad_path=bad,
            next_part_index=next_index,
            rollover_required=rollover,
        )
