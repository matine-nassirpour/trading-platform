from quantum.shared.serialization.schema_registry import REGISTRY


def test_registry_contains_known_events():
    assert "order_submit_v1" in REGISTRY
    assert "order_intent_v1" in REGISTRY
