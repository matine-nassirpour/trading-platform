import json
import logging
from collections.abc import Iterator
from pathlib import Path

import pytest

from quantum.adapters.telemetry.event_emitter import emit_event
from quantum.adapters.telemetry.logging.logs import LoggingConfig, init_logging
from quantum.foundation.events.trading.v1.order_submit_v1 import OrderSubmitV1


# --- Helpers -----------------------------------------------------------------
def _list_json_files(root: Path) -> list[Path]:
    return [p for p in root.rglob("*.json") if p.is_file()]


def _list_tmp_files(root: Path) -> list[Path]:
    return [p for p in root.rglob("*.tmp") if p.is_file()]


# --- Fixtures ----------------------------------------------------------------
@pytest.fixture
def tmp_audit_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """
    Configure the audit manager via QUANTUM_AUDIT_DIR (opt-in).
    We also isolate other log outputs to avoid polluting the local tree.
    """
    audit_root = tmp_path / "audit"
    audit_root.mkdir(parents=True)

    # Opt-in handlers via env variables
    monkeypatch.setenv("QUANTUM_AUDIT_DIR", str(audit_root))

    # No partition handler in these tests (avoids JSONL files)
    monkeypatch.delenv("QUANTUM_LOG_DIR", raising=False)

    # Traces in "none" for silence test
    monkeypatch.setenv("QUANTUM_TRACE_EXPORTER", "none")

    yield audit_root

    # Explicit cleanup if needed
    for p in audit_root.rglob("*"):
        try:
            if p.is_file():
                p.unlink()
        except Exception:
            pass


@pytest.fixture
def configured_logging(tmp_audit_dir: Path) -> None:
    """
    Initializes logging with the active audit handler.
    """
    init_logging(
        LoggingConfig(
            app_name="python_core",
            environment="dev",
            namespace="quantum",
            log_level="INFO",
        )
    )
    # Sanity: the root logger must exist with our handlers
    root = logging.getLogger()
    assert root.handlers, "root logger has no handlers after init_logging()"


# --- Tests -------------------------------------------------------------------


def test_audit_event_file_is_created_and_contains_event_payload(
    tmp_audit_dir: Path, configured_logging: None
) -> None:
    """
    An auditable event ('order_submit_v1') writes a single JSON file
    under <audit>/<env>/<ns>/<app>/YYYY/MM/DD/HHMMSS-UUID.json.
    The content is exactly the 'event' payload (with run_id/correlation_id
    injected by emit_event).
    """
    # Build a correct Pydantic model (RFC3339 ms timestamp required)
    event = OrderSubmitV1(
        timestamp="2025-09-29T14:12:45.123Z",
        app="ea_mql5",
        intent_id="intent-123",
        client_order_id="cid-456",
        symbol="EURUSD",
        request_ms=1695996765123,
        response_ms=None,
        request={"type": "market", "volume": 0.10},
        # Optional BaseEvent fields (run_id/correlation_id) will be injected
    )

    emit_event(event)

    # Search for a single JSON file (unit write)
    json_files = _list_json_files(tmp_audit_dir)
    assert len(json_files) == 1, f"expected 1 audit json file, got {len(json_files)}"

    # No .tmp files should remain (atomic write .tmp -> replace)
    tmp_files = _list_tmp_files(tmp_audit_dir)
    assert not tmp_files, f"temporary files should not remain: {tmp_files}"

    # Upload the file and check the contents
    payload = json.loads(json_files[0].read_text(encoding="utf-8"))

    # Event name must match
    assert payload["event_name"] == "order_submit_v1"

    # Input fields present
    assert payload["symbol"] == "EURUSD"
    assert payload["request"]["type"] == "market"

    # Fields injected by emit_event (present but values not precisely tested)
    assert "run_id" in payload
    assert "correlation_id" in payload

    # Robustness: no serialized exception in the audit
    assert "exception" not in payload, "audit payload should be the raw event only"


def test_non_audit_event_does_not_create_file(
    tmp_audit_dir: Path, configured_logging: None
) -> None:
    """
    An event not listed by AuditEventFilter should NOT create a file.
    """
    # 'trade_intent_v1' is NOT in AUDIT_EVENTS
    non_audit_event = {
        "event_name": "trade_intent_v1",
        "timestamp": "2025-09-29T14:12:45.123Z",
        "app": "python_core",
        "intent_id": "intent-na",
        "symbol": "XAUUSD",
        "side": "buy",
        "type": "market",
        "volume": 1.0,
    }

    emit_event(non_audit_event)

    json_files = _list_json_files(tmp_audit_dir)
    assert len(json_files) == 0, f"no audit file expected, found: {json_files}"


def test_log_without_event_extra_is_ignored_by_audit_handler(
    tmp_audit_dir: Path, configured_logging: None
) -> None:
    """
    A standard log (without extra['event']) should not be written by the audit handler.
    """
    logging.getLogger("quantum.trading").info("hello without event extra")
    assert _list_json_files(tmp_audit_dir) == []
