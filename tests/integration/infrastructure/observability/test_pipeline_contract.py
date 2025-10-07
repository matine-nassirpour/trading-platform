from __future__ import annotations

import json
import logging
import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import pytest

from quantum.infrastructure.observability.metrics import health as m

_NumberLike = float | int | str | bytes


# Prometheus Helpers (gets the value of a Gauge/Counter created by health.py)
def _gauge_value(g: Any) -> float:
    maybe_get = getattr(getattr(g, "_value", None), "get", None)
    if not callable(maybe_get):
        return -1.0
    try:
        return float(cast(Callable[[], _NumberLike], maybe_get)())
    except Exception:
        return -1.0


def _any_file(root: Path, pattern: str) -> Path | None:
    for p in root.rglob(pattern):
        return p
    return None


def _latest(root: Path, pattern: str) -> Path | None:
    files = list(root.rglob(pattern))
    if not files:
        return None
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0]


@pytest.mark.usefixtures("no_rate_limit_no_sampling")
def test_pipeline_contract(obs_session, tmp_workspace, assert_jsonl_tail):
    """
    Contract / Integration (top-down)

    - pipeline_up=1, pipeline_logging_ok=1, pipeline_tracing_ok=1, logging_sink_up=1
    - whitelist event emitted -> valid JSON audit file
    - INFO/WARN/CRITICAL log emitted -> JSONL present
        * severity mapping: WARNING→WARN(13), CRITICAL→FATAL(21)
        * redaction on attrs.secret -> "[REDACTED]"
    """
    # Sanity Prometheus health gauges
    assert _gauge_value(m.pipeline_logging_ok) == 1.0, "pipeline_logging_ok != 1"
    assert _gauge_value(m.pipeline_tracing_ok) == 1.0, "pipeline_tracing_ok != 1"
    # logging_sink_up measures **persistence** (partition/audit), not console:
    assert _gauge_value(m.logging_sink_up) == 1.0, "logging_sink_up != 1"
    assert _gauge_value(m.pipeline_up) == 1.0, "pipeline_up != 1"

    # Issue an audit event whitelist (order_submit_v1)
    from quantum.infrastructure.observability.logging.event_emitter import emit_event

    emit_event(
        {
            "event_name": "order_submit_v1",
            "event_version": "v1",
            "order_id": "ct-1",
            "symbol": "EURUSD",
            "side": "buy",
            "qty": 1.0,
            "price": 1.23456,
            "ts": int(time.time() * 1000),
        }
    )

    # Issue logs at different levels + secrecy for redaction
    log = logging.getLogger("contract")
    log.info(
        "contract start",
        extra={
            "attrs": {
                "probe": "ok",
                "secret": "thisisafakesecret",  # pragma: allowlist secret
            }
        },
    )
    log.warning("severity probe warning")
    log.critical("severity probe critical")

    # Assertions on JSONL (tail)
    logs_dir: Path = tmp_workspace["logs"]
    # presence of key entries
    start_hits = assert_jsonl_tail(
        logs_dir,
        match=lambda o: o.get("message") == "contract start",
        min_count=1,
    )
    warn_hits = assert_jsonl_tail(
        logs_dir,
        match=lambda o: o.get("message") == "severity probe warning",
        min_count=1,
    )
    crit_hits = assert_jsonl_tail(
        logs_dir,
        match=lambda o: o.get("message") == "severity probe critical",
        min_count=1,
    )

    start_obj = start_hits[0]
    warn_obj = warn_hits[0]
    crit_obj = crit_hits[0]

    # essential fields present
    for obj in (start_obj, warn_obj, crit_obj):
        for key in (
            "service_name",
            "service_namespace",
            "service_version",
            "timestamp",
            "level",
            "logger",
            "message",
            "attrs",
        ):
            assert key in obj, f"missing field {key!r} in JSON log"

    # writing applied to attrs.secret
    attrs = start_obj.get("attrs", {})
    assert attrs.get("secret") == "[REDACTED]", "redaction not applied on attrs.secret"

    # severity mapping (text + OTel number)
    def _assert_sev(obj: dict, expected_level: str, expected_num: int) -> None:
        lvl = obj.get("level")
        num = obj.get("severity_number")
        assert lvl == expected_level, f"expected level={expected_level}, got {lvl!r}"
        assert isinstance(num, int), "severity_number missing/not int"
        assert 1 <= num <= 24, f"severity_number out of range: {num}"
        assert (
            num == expected_num
        ), f"unexpected severity_number: got {num}, want {expected_num}"

    _assert_sev(warn_obj, "WARN", 13)
    _assert_sev(crit_obj, "FATAL", 21)

    # Assertions on the audit file
    audit_dir: Path = tmp_workspace["audit"]
    # the audit file is written under <base>/<env>/<namespace>/<app>/<YYYY>/<MM>/<DD>/<HHMMSS-UUID>.json
    env_ = os.environ.get("QUANTUM_ENV", "test")
    ns = os.environ.get("QUANTUM_NS", "quantum")
    app = os.environ.get("QUANTUM_APP_NAME", "test_app")

    # Check for the presence of a .json in the expected tree structure
    nested_root = audit_dir / env_ / ns / app
    any_audit = _any_file(nested_root, "*.json")
    if any_audit is None:
        # we re-sweep everything _audit by tolerance
        any_audit = _any_file(audit_dir, "*.json")
    assert any_audit is not None, "no audit file generated"

    # Readable and good JSON event_name
    data = json.loads(any_audit.read_text(encoding="utf-8"))
    assert data.get("event_name") == "order_submit_v1", "invalid audit file payload"

    # A recent events-*.jsonl file does exist
    latest_events = _latest(logs_dir, "events-*.jsonl")
    assert latest_events is not None, "no events-*.jsonl produced"
