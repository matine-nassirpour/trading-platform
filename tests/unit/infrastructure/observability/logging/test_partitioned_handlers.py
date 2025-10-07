from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

import pytest

from quantum.infrastructure.observability.logging.partitioned_handlers import (
    PartitionedJSONLFileHandler,
)


def _ts(dt: datetime) -> float:
    return dt.replace(tzinfo=timezone.utc).timestamp()


class _EchoFormatter(logging.Formatter):
    """Formatter simple qui renvoie exactement le message du LogRecord."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        return record.getMessage()


class _BoomFormatter(logging.Formatter):
    """Formatter qui lève une exception pour tester la quarantaine."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        raise ValueError("formatting failed (synthetic)")


def _make_record(msg: str, *, created_ts: float) -> logging.LogRecord:
    rec = logging.LogRecord(
        name="t",
        level=logging.INFO,
        pathname="x.py",
        lineno=1,
        msg=msg,
        args=(),
        exc_info=None,
    )
    rec.created = created_ts
    return rec


@pytest.mark.usefixtures("iso_env", "_auto_cleanup_handlers", "clean_registry")
class TestPartitionedJSONLFileHandler:
    def test_writes_to_expected_partition_and_filename(
        self, tmp_path: Path, monkeypatch
    ):
        # Pas de rollover
        monkeypatch.setenv("QUANTUM_LOG_MAX_BYTES", "0")
        monkeypatch.setenv("QUANTUM_LOG_WARN_BYTES", "0")
        monkeypatch.setenv("QUANTUM_LOG_FSYNC", "0")

        base = tmp_path / "_logs"
        dt = datetime(2025, 10, 7, 12, 34, 56, tzinfo=timezone.utc)
        ts = _ts(dt)

        h = PartitionedJSONLFileHandler(
            base_dir=str(base),
            app="appx",
            environment="dev",
            namespace="quantum",
        )
        h.setFormatter(_EchoFormatter())

        # Émission
        msg = "M" * 20
        rec = _make_record(msg, created_ts=ts)
        h.emit(rec)
        h.close()

        # Chemin attendu
        yyyy = dt.strftime("%Y")
        mm = dt.strftime("%m")
        dd = dt.strftime("%d")
        hh = dt.strftime("%H")
        expected_dir = base / "dev" / "quantum" / "appx" / yyyy / mm / dd / hh
        expected_file = expected_dir / f"events-{yyyy}{mm}{dd}-{hh}.jsonl"

        assert expected_file.exists(), f"missing {expected_file}"
        content = expected_file.read_text(encoding="utf-8").strip().splitlines()
        assert content == [msg]

    def test_rollover_creates_part1_when_size_exceeded(
        self, tmp_path: Path, monkeypatch
    ):
        # Rollover agressif
        monkeypatch.setenv("QUANTUM_LOG_MAX_BYTES", "120")  # petit seuil
        monkeypatch.setenv("QUANTUM_LOG_WARN_BYTES", "0")
        monkeypatch.setenv("QUANTUM_LOG_FSYNC", "0")

        base = tmp_path / "_logs"
        dt = datetime(2025, 10, 7, 13, 0, 0, tzinfo=timezone.utc)
        ts = _ts(dt)

        h = PartitionedJSONLFileHandler(
            base_dir=str(base),
            app="appx",
            environment="dev",
            namespace="quantum",
        )
        h.setFormatter(_EchoFormatter())

        # Messages assez longs pour dépasser ~120 octets au total
        for i in range(5):
            rec = _make_record(f"{i}-" + ("X" * 60), created_ts=ts)
            h.emit(rec)

        h.close()

        yyyy = dt.strftime("%Y")
        mm = dt.strftime("%m")
        dd = dt.strftime("%d")
        hh = dt.strftime("%H")
        d = base / "dev" / "quantum" / "appx" / yyyy / mm / dd / hh
        files = {p.name for p in d.glob("*.jsonl")}
        # On attend au moins la base et un .part1
        assert f"events-{yyyy}{mm}{dd}-{hh}.jsonl" in files
        assert f"events-{yyyy}{mm}{dd}-{hh}.part1.jsonl" in files

    def test_bad_logs_quarantine_when_formatter_raises(
        self, tmp_path: Path, monkeypatch
    ):
        monkeypatch.setenv("QUANTUM_LOG_MAX_BYTES", "0")
        monkeypatch.setenv("QUANTUM_LOG_WARN_BYTES", "0")
        monkeypatch.setenv("QUANTUM_LOG_FSYNC", "0")

        base = tmp_path / "_logs"
        dt = datetime(2025, 10, 7, 14, 0, 0, tzinfo=timezone.utc)
        ts = _ts(dt)

        h = PartitionedJSONLFileHandler(
            base_dir=str(base),
            app="appx",
            environment="dev",
            namespace="quantum",
        )
        h.setFormatter(_BoomFormatter())

        rec = _make_record("will fail in formatter", created_ts=ts)
        # emit → format() lève → écrit en quarantaine bad-logs-*.jsonl
        h.emit(rec)
        h.close()

        yyyy = dt.strftime("%Y")
        mm = dt.strftime("%m")
        dd = dt.strftime("%d")
        hh = dt.strftime("%H")
        d = base / "dev" / "quantum" / "appx" / yyyy / mm / dd / hh
        bads = list(d.glob(f"bad-logs-{yyyy}{mm}{dd}-{hh}*.jsonl"))
        assert bads, "expected a bad-logs file to exist"
        # JSON minimal avec la raison
        content = bads[0].read_text(encoding="utf-8").strip().splitlines()
        assert content, "bad-logs should contain at least one line"

    def test_fsync_enabled_does_not_crash(self, tmp_path: Path, monkeypatch):
        # On ne peut pas vérifier fsync réellement, on s'assure juste qu'aucune exception n'est levée.
        monkeypatch.setenv("QUANTUM_LOG_MAX_BYTES", "0")
        monkeypatch.setenv("QUANTUM_LOG_WARN_BYTES", "0")
        monkeypatch.setenv("QUANTUM_LOG_FSYNC", "1")

        base = tmp_path / "_logs"
        dt = datetime(2025, 10, 7, 15, 0, 0, tzinfo=timezone.utc)
        ts = _ts(dt)

        h = PartitionedJSONLFileHandler(
            base_dir=str(base),
            app="appx",
            environment="dev",
            namespace="quantum",
        )
        h.setFormatter(_EchoFormatter())

        rec = _make_record("fsync path", created_ts=ts)
        h.emit(rec)
        h.close()

        # existence d'au moins 1 fichier events
        yyyy = dt.strftime("%Y")
        mm = dt.strftime("%m")
        dd = dt.strftime("%d")
        hh = dt.strftime("%H")
        d = base / "dev" / "quantum" / "appx" / yyyy / mm / dd / hh
        assert list(d.glob("events-*.jsonl")), "expected an events file"
