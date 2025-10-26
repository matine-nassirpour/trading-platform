from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import pytest

import quantum.infrastructure.observability.logging.handlers.audit_sink_handler as audit_mod
from quantum.infrastructure.observability.logging.handlers.audit_sink_handler import (
    AuditEventFileHandler,
)
from tests.support.factories import make_record
from tests.support.time_utils import to_timestamp


@pytest.mark.usefixtures("iso_env", "clean_registry")
class TestAuditEventFileHandler:
    def test_writes_single_json_event_atomically(self, tmp_path: Path):
        """
        Given a valid event payload
        When emitting through AuditEventFileHandler
        Then exactly one JSON file is written atomically with the exact payload
        And the file resides under <base>/<env>/<ns>/<app>/YYYY/MM/DD/
        """
        # Arrange
        base = tmp_path / "_audit"
        dt = datetime(2025, 10, 7, 16, 12, 34, tzinfo=timezone.utc)
        ts = to_timestamp(dt)

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
        rec = make_record(
            name="quantum.trading",
            level=logging.INFO,
            msg=event.get("event_name") or "event",
            created_ts=ts,
            event=event,
        )

        # Act
        h.emit(rec)
        h.close()

        # Assert: file exists and JSON matches exactly
        root = base / "dev" / "quantum" / "appx"
        files = list(root.rglob("*.json"))
        assert files, f"no audit json file under {root}"
        js = json.loads(files[0].read_text(encoding="utf-8"))
        assert js == event, "audit JSON must be exactly the emitted event"

        # Assert: directory hierarchy matches the timestamped partition
        yyyy = dt.strftime("%Y")
        mm = dt.strftime("%m")
        dd = dt.strftime("%d")
        expected_dir = root / yyyy / mm / dd
        assert files[0].parent == expected_dir, (
            f"unexpected directory layout; expected {expected_dir}, "
            f"got {files[0].parent}"
        )

    def test_disk_error_path_calls_inc_counter_and_cleans_tmp(
        self, tmp_path: Path, monkeypatch
    ):
        """
        Given os.replace fails during the atomic write
        When emit() handles the exception path
        Then inc_disk_error_counter() is called
        And no temporary *.tmp files are left behind
        """
        # Arrange
        base = tmp_path / "_audit"
        dt = datetime(2025, 10, 7, 17, 0, 0, tzinfo=timezone.utc)
        ts = to_timestamp(dt)

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
        rec = make_record(
            name="quantum.trading",
            level=logging.INFO,
            msg=event.get("event_name") or "event",
            created_ts=ts,
            event=event,
        )

        called = {"n": 0}

        def _inc():
            called["n"] += 1

        # Monkeypatch module-level counter increment
        monkeypatch.setattr(audit_mod, "inc_disk_error_counter", _inc, raising=True)

        # Force the atomic replacement step to fail to trigger the exception branch
        def _boom_replace(*_args, **_kwargs):
            raise OSError("iofail")

        monkeypatch.setattr(audit_mod.os, "replace", _boom_replace, raising=True)

        # Act
        h.emit(rec)
        h.close()

        # Assert
        assert called["n"] >= 1, "inc_disk_error_counter should have been called"

        # Assert: no temporary leftovers
        leftovers = list((base / "dev" / "quantum" / "appx").rglob("*.tmp"))
        assert (
            not leftovers
        ), f"temporary files should be cleaned up, found: {leftovers}"
