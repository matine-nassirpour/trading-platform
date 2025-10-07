from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import pytest

import quantum.infrastructure.observability.logging.audit_sink as audit_mod
from quantum.infrastructure.observability.logging.audit_sink import (
    AuditEventFileHandler,
)


def _ts(dt: datetime) -> float:
    return dt.replace(tzinfo=timezone.utc).timestamp()


def _make_record(event: dict, *, created_ts: float) -> logging.LogRecord:
    rec = logging.LogRecord(
        name="quantum.trading",
        level=logging.INFO,
        pathname="x.py",
        lineno=1,
        msg=event.get("event_name") or "event",
        args=(),
        exc_info=None,
    )
    rec.created = created_ts
    # handler lit record.event (dict)
    setattr(rec, "event", event)
    return rec


@pytest.mark.usefixtures("iso_env", "clean_registry")
class TestAuditEventFileHandler:
    def test_writes_single_json_event_atomically(self, tmp_path: Path):
        base = tmp_path / "_audit"
        dt = datetime(2025, 10, 7, 16, 12, 34, tzinfo=timezone.utc)
        ts = _ts(dt)

        h = AuditEventFileHandler(
            base_dir=str(base),
            app="appx",
            environment="dev",
            namespace="quantum",
        )

        event = {
            "event_name": "order_submit_v1",
            "schema_version": 1,
            "order_id": "u-1",
            "ts": int(ts * 1000),
        }

        rec = _make_record(event, created_ts=ts)
        h.emit(rec)
        h.close()

        # Fichier généré quelque part sous base/dev/quantum/appx/YYYY/MM/DD/
        root = base / "dev" / "quantum" / "appx"
        files = list(root.rglob("*.json"))
        assert files, f"no audit json file under {root}"
        js = json.loads(files[0].read_text(encoding="utf-8"))
        assert js == event

    def test_disk_error_path_calls_inc_counter_and_cleans_tmp(
        self, tmp_path: Path, monkeypatch
    ):
        """
        Force une erreur pendant l'emit → inc_disk_error_counter() doit être appelé
        et le .tmp ne doit pas rester.
        """
        base = tmp_path / "_audit"
        dt = datetime(2025, 10, 7, 17, 0, 0, tzinfo=timezone.utc)
        ts = _ts(dt)

        h = AuditEventFileHandler(
            base_dir=str(base),
            app="appx",
            environment="dev",
            namespace="quantum",
        )

        event = {
            "event_name": "order_submit_v1",
            "order_id": "boom",
            "ts": int(ts * 1000),
        }
        rec = _make_record(event, created_ts=ts)

        called = {"n": 0}

        def _inc():
            called["n"] += 1

        # Remplace inc_disk_error_counter dans le module du handler
        monkeypatch.setattr(audit_mod, "inc_disk_error_counter", _inc, raising=True)

        # Provoque l'échec atomique (remplacement) pour entrer dans le except
        def _boom_replace(*args, **kwargs):
            raise OSError("iofail")

        monkeypatch.setattr(audit_mod.os, "replace", _boom_replace, raising=True)

        # Exécute
        h.emit(rec)
        h.close()

        assert called["n"] >= 1, "inc_disk_error_counter should have been called"

        # Assure qu'aucun .tmp ne traîne
        tmp_leftovers = list((base / "dev" / "quantum" / "appx").rglob("*.tmp"))
        assert (
            not tmp_leftovers
        ), f"tmp files should be cleaned up, found: {tmp_leftovers}"
