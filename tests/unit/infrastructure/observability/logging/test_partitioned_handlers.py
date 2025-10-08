from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

import pytest

from quantum.infrastructure.observability.logging.partitioned_handlers import (
    PartitionedJSONLFileHandler,
)
from tests.support.factories import make_record
from tests.support.time_utils import to_timestamp

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


class _EchoFormatter(logging.Formatter):
    """Formatter that returns exactly the LogRecord message."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        return record.getMessage()


class _BoomFormatter(logging.Formatter):
    """Formatter that raises to test quarantine path."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        raise ValueError("formatting failed (synthetic)")


def _partition_dir(base: Path, *, env: str, ns: str, app: str, dt: datetime) -> Path:
    """
    Return <base>/<env>/<ns>/<app>/YYYY/MM/DD/HH for a given UTC datetime.
    """
    yyyy = dt.strftime("%Y")
    mm = dt.strftime("%m")
    dd = dt.strftime("%d")
    hh = dt.strftime("%H")
    return base / env / ns / app / yyyy / mm / dd / hh


def _events_filename(dt: datetime, *, part: int | None = None) -> str:
    """
    Return the canonical events filename for a given datetime and optional part index.
    Example: events-20251007-12.jsonl or events-20251007-12.part1.jsonl
    """
    stem = dt.strftime("events-%Y%m%d-%H")
    return f"{stem}.part{part}.jsonl" if part is not None else f"{stem}.jsonl"


def _badlogs_glob(dt: datetime) -> str:
    """
    Return a glob pattern for quarantine files for the given datetime hour.
    Example: bad-logs-20251007-12*.jsonl
    """
    return dt.strftime("bad-logs-%Y%m%d-%H*.jsonl")


# ──────────────────────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.usefixtures("iso_env", "_auto_cleanup_handlers", "clean_registry")
class TestPartitionedJSONLFileHandler:
    def test_writes_to_expected_partition_and_filename(
        self, tmp_path: Path, monkeypatch
    ):
        """
        Given QUANTUM_LOG_MAX_BYTES=0 (no rollover)
        When emitting a single record through PartitionedJSONLFileHandler
        Then a file 'events-YYYYMMDD-HH.jsonl' is created under
             <base>/<env>/<ns>/<app>/YYYY/MM/DD/HH with the exact message
        """
        # Arrange
        monkeypatch.setenv("QUANTUM_LOG_MAX_BYTES", "0")
        monkeypatch.setenv("QUANTUM_LOG_WARN_BYTES", "0")
        monkeypatch.setenv("QUANTUM_LOG_FSYNC", "0")

        base = tmp_path / "_logs"
        dt = datetime(2025, 10, 7, 12, 34, 56, tzinfo=timezone.utc)
        ts = to_timestamp(dt)

        h = PartitionedJSONLFileHandler(
            base_dir=str(base),
            app="appx",
            environment="dev",
            namespace="quantum",
        )
        h.setFormatter(_EchoFormatter())

        # Act
        msg = "M" * 20
        rec = make_record(msg=msg, created_ts=ts)
        h.emit(rec)
        h.close()

        # Assert: expected path and content
        expected_dir = _partition_dir(base, env="dev", ns="quantum", app="appx", dt=dt)
        expected_file = expected_dir / _events_filename(dt)

        assert expected_file.exists(), f"missing {expected_file}"
        content = expected_file.read_text(encoding="utf-8").strip().splitlines()
        assert content == [msg]

    def test_rollover_creates_part1_when_size_exceeded(
        self, tmp_path: Path, monkeypatch
    ):
        """
        Given a small QUANTUM_LOG_MAX_BYTES threshold
        When enough long messages are emitted
        Then a rollover occurs and '.part1' file appears alongside the base file
        """
        # Arrange
        monkeypatch.setenv("QUANTUM_LOG_MAX_BYTES", "120")  # small threshold
        monkeypatch.setenv("QUANTUM_LOG_WARN_BYTES", "0")
        monkeypatch.setenv("QUANTUM_LOG_FSYNC", "0")

        base = tmp_path / "_logs"
        dt = datetime(2025, 10, 7, 13, 0, 0, tzinfo=timezone.utc)
        ts = to_timestamp(dt)

        h = PartitionedJSONLFileHandler(
            base_dir=str(base),
            app="appx",
            environment="dev",
            namespace="quantum",
        )
        h.setFormatter(_EchoFormatter())

        # Act: long messages to exceed ~120 bytes total
        for i in range(5):
            rec = make_record(msg=f"{i}-" + ("X" * 60), created_ts=ts)
            h.emit(rec)
        h.close()

        # Assert
        d = _partition_dir(base, env="dev", ns="quantum", app="appx", dt=dt)
        files = {p.name for p in d.glob("*.jsonl")}
        assert _events_filename(dt) in files
        assert _events_filename(dt, part=1) in files

    def test_bad_logs_quarantine_when_formatter_raises(
        self, tmp_path: Path, monkeypatch
    ):
        """
        Given a formatter that raises
        When emitting a record
        Then a quarantine 'bad-logs-YYYYMMDD-HH*.jsonl' file is written
        """
        monkeypatch.setenv("QUANTUM_LOG_MAX_BYTES", "0")
        monkeypatch.setenv("QUANTUM_LOG_WARN_BYTES", "0")
        monkeypatch.setenv("QUANTUM_LOG_FSYNC", "0")

        base = tmp_path / "_logs"
        dt = datetime(2025, 10, 7, 14, 0, 0, tzinfo=timezone.utc)
        ts = to_timestamp(dt)

        h = PartitionedJSONLFileHandler(
            base_dir=str(base),
            app="appx",
            environment="dev",
            namespace="quantum",
        )
        h.setFormatter(_BoomFormatter())

        rec = make_record(msg="will fail in formatter", created_ts=ts)

        # Act: emit → format() raises → quarantine write
        h.emit(rec)
        h.close()

        # Assert: quarantine file exists and contains at least one line
        d = _partition_dir(base, env="dev", ns="quantum", app="appx", dt=dt)
        bads = list(d.glob(_badlogs_glob(dt)))
        assert bads, "expected a bad-logs file to exist"

        content = bads[0].read_text(encoding="utf-8").strip().splitlines()
        assert content, "bad-logs should contain at least one line"

    def test_fsync_enabled_does_not_crash(self, tmp_path: Path, monkeypatch):
        """
        Given QUANTUM_LOG_FSYNC=1
        When emitting a record
        Then no exception is raised and at least one events file exists
        """
        monkeypatch.setenv("QUANTUM_LOG_MAX_BYTES", "0")
        monkeypatch.setenv("QUANTUM_LOG_WARN_BYTES", "0")
        monkeypatch.setenv("QUANTUM_LOG_FSYNC", "1")

        base = tmp_path / "_logs"
        dt = datetime(2025, 10, 7, 15, 0, 0, tzinfo=timezone.utc)
        ts = to_timestamp(dt)

        h = PartitionedJSONLFileHandler(
            base_dir=str(base),
            app="appx",
            environment="dev",
            namespace="quantum",
        )
        h.setFormatter(_EchoFormatter())

        rec = make_record(msg="fsync path", created_ts=ts)
        h.emit(rec)
        h.close()

        # Assert: at least one events-*.jsonl exists
        d = _partition_dir(base, env="dev", ns="quantum", app="appx", dt=dt)
        assert list(d.glob("events-*.jsonl")), "expected an events file"
