from __future__ import annotations

import logging

from datetime import UTC, datetime
from pathlib import Path

import pytest

from quantum.infrastructure.observability.logging.handlers.partitioned_handler import (
    PartitionedJSONLFileHandler,
)
from tests.support.factories import make_record
from tests.support.time_utils import to_timestamp

# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Helpers                                                                     │
# ╰─────────────────────────────────────────────────────────────────────────────╯


class _EchoFormatter(logging.Formatter):
    """Formatter that returns exactly the LogRecord message."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        return record.getMessage()


class _BoomFormatter(logging.Formatter):
    """Formatter that raises to test quarantine path."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        raise ValueError("formatting failed (synthetic)")


def _partition_dir(base: Path, *, env: str, ns: str, app: str, dt: datetime) -> Path:
    """Return <base>/<env>/<ns>/<app>/YYYY/MM/DD/HH for a given UTC datetime."""
    yyyy = dt.strftime("%Y")
    mm = dt.strftime("%m")
    dd = dt.strftime("%d")
    hh = dt.strftime("%H")
    return base / env / ns / app / yyyy / mm / dd / hh


def _events_filename(dt: datetime, *, part: int | None = None) -> str:
    """Return canonical events filename for a given datetime and optional part index."""
    stem = dt.strftime("events-%Y%m%d-%H")
    return f"{stem}.part{part}.jsonl" if part is not None else f"{stem}.jsonl"


def _badlogs_glob(dt: datetime) -> str:
    """Return a glob pattern for quarantine files for the given datetime hour."""
    return dt.strftime("bad-logs-%Y%m%d-%H*.jsonl")


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Tests                                                                       │
# ╰─────────────────────────────────────────────────────────────────────────────╯


@pytest.mark.unit
@pytest.mark.usefixtures("iso_env", "_auto_cleanup_handlers", "clean_registry")
class TestPartitionedJSONLFileHandler:
    def test_writes_to_expected_partition_and_filename(
        self, tmp_path: Path, base_settings, make_observability
    ):
        """Ensure correct partition and filename when writing one record."""
        obs = make_observability()
        dt = datetime(2025, 10, 7, 12, 34, 56, tzinfo=UTC)
        ts = to_timestamp(dt)

        h = PartitionedJSONLFileHandler(base_settings, obs)
        h.setFormatter(_EchoFormatter())

        msg = "M" * 20
        rec = make_record(msg=msg, created_ts=ts)
        h.emit(rec)
        h.close()

        expected_dir = _partition_dir(
            Path(obs.quantum_log_dir),
            env=base_settings.quantum_env,
            ns=base_settings.quantum_ns,
            app=base_settings.quantum_app_name,
            dt=dt,
        )
        expected_file = expected_dir / _events_filename(dt)

        assert expected_file.exists(), f"missing {expected_file}"
        content = expected_file.read_text(encoding="utf-8").strip().splitlines()
        assert content == [msg]

    def test_rollover_creates_part1_when_size_exceeded(
        self, tmp_path: Path, base_settings, make_observability
    ):
        """Rollover creates '.part1' file once size threshold exceeded."""
        obs = make_observability(quantum_log_max_bytes=120)
        dt = datetime(2025, 10, 7, 13, 0, 0, tzinfo=UTC)
        ts = to_timestamp(dt)

        h = PartitionedJSONLFileHandler(base_settings, obs)
        h.setFormatter(_EchoFormatter())

        for i in range(5):
            rec = make_record(msg=f"{i}-" + ("X" * 60), created_ts=ts)
            h.emit(rec)
        h.close()

        d = _partition_dir(
            Path(obs.quantum_log_dir),
            env=base_settings.quantum_env,
            ns=base_settings.quantum_ns,
            app=base_settings.quantum_app_name,
            dt=dt,
        )
        files = {p.name for p in d.glob("*.jsonl")}
        assert _events_filename(dt) in files
        assert _events_filename(dt, part=1) in files

    def test_bad_logs_quarantine_when_formatter_raises(
        self, tmp_path: Path, base_settings, make_observability
    ):
        """Malformed log entries go to quarantine file."""
        obs = make_observability()
        dt = datetime(2025, 10, 7, 14, 0, 0, tzinfo=UTC)
        ts = to_timestamp(dt)

        h = PartitionedJSONLFileHandler(base_settings, obs)
        h.setFormatter(_BoomFormatter())

        rec = make_record(msg="will fail in formatter", created_ts=ts)
        h.emit(rec)
        h.close()

        d = _partition_dir(
            Path(obs.quantum_log_dir),
            env=base_settings.quantum_env,
            ns=base_settings.quantum_ns,
            app=base_settings.quantum_app_name,
            dt=dt,
        )
        bads = list(d.glob(_badlogs_glob(dt)))
        assert bads, "expected a bad-logs file to exist"

        content = bads[0].read_text(encoding="utf-8").strip().splitlines()
        assert content, "bad-logs should contain at least one line"

    def test_fsync_enabled_does_not_crash(
        self, tmp_path: Path, base_settings, make_observability
    ):
        """fsync path executes safely without error."""
        obs = make_observability(quantum_log_fsync=True)
        dt = datetime(2025, 10, 7, 15, 0, 0, tzinfo=UTC)
        ts = to_timestamp(dt)

        h = PartitionedJSONLFileHandler(base_settings, obs)
        h.setFormatter(_EchoFormatter())

        rec = make_record(msg="fsync path", created_ts=ts)
        h.emit(rec)
        h.close()

        d = _partition_dir(
            Path(obs.quantum_log_dir),
            env=base_settings.quantum_env,
            ns=base_settings.quantum_ns,
            app=base_settings.quantum_app_name,
            dt=dt,
        )
        assert list(d.glob("events-*.jsonl")), "expected an events file"
