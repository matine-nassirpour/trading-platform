import json

from quantum.foundation.serialization.schema_registry import REGISTRY


def test_registry_contains_known_events():
    assert "order_submit_v1" in REGISTRY
    assert "trade_intent_v1" in REGISTRY


def test_validate_golden_example():
    payload = {
        "event_name": "order_submit_v1",
        "timestamp": "2025-01-01T00:00:00.000Z",
        "log_schema_version": "v1",
        "app": "ea_mql5",
        "intent_id": "iid-123",
        "client_order_id": "coid-456",
        "symbol": "EURUSD",
        "request_ms": 1735689600000,
        "response_ms": None,
        "request": {"type": "ORDER_TYPE_BUY"},
    }
    model_cls = REGISTRY[payload["event_name"]]
    m = model_cls.model_validate(payload)
    # round-trip JSON
    s = m.model_dump_json()
    dd = json.loads(s)
    assert dd["event_name"] == "order_submit_v1"
