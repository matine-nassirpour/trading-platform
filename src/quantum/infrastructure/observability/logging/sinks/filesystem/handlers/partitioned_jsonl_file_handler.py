from __future__ import annotations

import logging

from contextlib import suppress
from typing import Final

from quantum.infrastructure.observability.logging.runtime.metrics import define_counter
from quantum.infrastructure.observability.logging.sinks.filesystem.formatters.jsonl_formatter import (
    RecordFormatter,
)
from quantum.infrastructure.observability.logging.sinks.filesystem.policies.partition_policy import (
    PartitionPolicy,
)
from quantum.infrastructure.observability.logging.sinks.filesystem.writers.quarantine_writer import (
    QuarantineWriter,
)
from quantum.infrastructure.observability.logging.sinks.filesystem.writers.safe_file_writer import (
    SafeFileWriter,
)

_LOGGING_DISK_ERRORS: Final = define_counter("logging_disk_errors")
_LOGGING_FILE_ROTATIONS: Final = define_counter("logging_file_rotations")


class PartitionedJSONLFileHandler(logging.Handler):
    """
    Safety-grade handler:
    - zero business logic
    - no directory logic
    - no formatting logic
    - no rotation policy
    - no quarantine logic
    Only orchestrates injected components.
    """

    def __init__(
        self,
        *,
        formatter: RecordFormatter,
        policy: PartitionPolicy,
    ) -> None:
        super().__init__()
        self._formatter = formatter
        self._policy = policy

        self._writer = SafeFileWriter()
        self._quarantine = QuarantineWriter()

        self._current_part = 0

    def emit(self, record: logging.LogRecord) -> None:
        self.acquire()
        try:
            ts = record.created
            size = self._writer.size()
            decision = self._policy.decide(
                record_timestamp=ts,
                part_index=self._current_part,
                current_path=self._writer.path,
                current_size=size,
            )

            # rotation if needed
            if decision.rollover_required or self._writer.path != decision.events_path:
                with suppress(Exception):
                    self._writer.close()
                    self._quarantine.close()
                self._writer.open_append(decision.events_path)
                self._quarantine.open(decision.bad_path)
                self._current_part = (
                    0 if decision.rollover_required else self._current_part
                )
                _LOGGING_FILE_ROTATIONS.inc()

            # try writing
            line = self._formatter.format(record)
            try:
                self._writer.write_line(line)
            except Exception as err:
                _LOGGING_DISK_ERRORS.inc()
                self._quarantine.write_error(
                    {
                        "error": str(err),
                        "logger": record.name,
                        "level": record.levelname,
                        "message": "<format_failed>",
                    }
                )
        finally:
            self.release()

    def close(self) -> None:
        self.acquire()
        try:
            with suppress(Exception):
                self._writer.close()
            with suppress(Exception):
                self._quarantine.close()
        finally:
            self.release()
        super().close()
