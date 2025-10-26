from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path

import pytest

from quantum.core.config.runtime.manager import ConfigManager
from quantum.infrastructure.observability.bootstrap.health_registry import (
    get_health_registry,
)


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
    - whitelist event emitted → valid JSON audit file
    - INFO/WARN/CRITICAL log emitted → JSONL present
        * severity mapping: WARNING→WARN(13), CRITICAL→FATAL(21)
        * redaction on attrs.secret → "[REDACTED]"
    """
    registry = get_health_registry()
    core_settings = ConfigManager.load()

    # Health gauges
    assert registry.pipeline_logging_ok._value.get() == 1.0, "pipeline_logging_ok != 1"
    assert registry.pipeline_tracing_ok._value.get() == 1.0, "pipeline_tracing_ok != 1"
    assert registry.logging_sink_up._value.get() == 1.0, "logging_sink_up != 1"

    metrics_enabled = core_settings.quantum_metrics_port > 0
    expected_pipeline_up = 1.0 if metrics_enabled else 0.0
    assert (
        registry.pipeline_up._value.get() == expected_pipeline_up
    ), f"pipeline_up should be {expected_pipeline_up} (metrics_enabled={metrics_enabled})"

    # Emit an allowlisted audit event
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

    # Logs at different levels + secret for redaction
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

    # Assertions on JSONL tail
    logs_dir: Path = tmp_workspace["logs"]

    start_hits = assert_jsonl_tail(
        logs_dir, match=lambda o: o.get("message") == "contract start", min_count=1
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

    # Essential fields present
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

    # Redaction applied to attrs.secret
    attrs = start_obj.get("attrs", {})
    assert attrs.get("secret") == "[REDACTED]", "redaction not applied on attrs.secret"

    # Severity mapping (text + OTel number)
    def _assert_sev(entry: dict, expected_level: str, expected_num: int) -> None:
        lvl = entry.get("level")
        num = entry.get("severity_number")
        assert lvl == expected_level, f"expected level={expected_level}, got {lvl!r}"
        assert isinstance(num, int), "severity_number missing/not int"
        assert 1 <= num <= 24, f"severity_number out of range: {num}"
        assert (
            num == expected_num
        ), f"unexpected severity_number: got {num}, want {expected_num}"

    _assert_sev(warn_obj, "WARN", 13)
    _assert_sev(crit_obj, "FATAL", 21)

    # Audit file presence under <base>/<env>/<ns>/<app>/YYYY/MM/DD/...
    audit_dir: Path = tmp_workspace["audit"]
    env_ = os.environ.get("QUANTUM_ENV", "test")
    ns = os.environ.get("QUANTUM_NS", "quantum")
    app = os.environ.get("QUANTUM_APP_NAME", "test_app")

    nested_root = audit_dir / env_ / ns / app
    any_audit = _any_file(nested_root, "*.json")
    if any_audit is None:
        any_audit = _any_file(audit_dir, "*.json")
    assert any_audit is not None, "no audit file generated"

    # JSON is valid and event_name ok
    data = json.loads(any_audit.read_text(encoding="utf-8"))
    assert data.get("event_name") == "order_submit_v1", "invalid audit file payload"

    # A recent events-*.jsonl file exists
    latest_events = _latest(logs_dir, "events-*.jsonl")
    assert latest_events is not None, "no events-*.jsonl produced"
