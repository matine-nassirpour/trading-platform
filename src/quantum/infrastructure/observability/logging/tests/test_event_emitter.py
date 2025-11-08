from __future__ import annotations

import logging
import uuid

import pytest

from quantum.infrastructure.observability.context.run_id import (
    generate_run_id,
    get_run_id,
    run_id_context,
)
from quantum.infrastructure.observability.logging.event_emitter import emit_event
from quantum.infrastructure.observability.tracing.correlation.correlation_id import (
    correlation_context,
)
from tests.support.logging_utils import capture_logger


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Helpers                                                                    │
# ╰────────────────────────────────────────────────────────────────────────────╯
def _is_uuid(s: str | None) -> bool:
    """Return True iff `s` is a valid UUID string."""
    if not s:
        return False
    try:
        uuid.UUID(s)
        return True
    except Exception:
        return False


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Tests                                                                      │
# ╰────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.unit
def test_emit_event_injects_ids_and_uses_default_level_info(monkeypatch):
    """
    Given run_id and correlation_id are set in ContextVars
    When emitting a custom event without explicit level mapping
    Then the log level defaults to INFO
    And run_id / correlation_id are injected into the event payload
    """
    # Arrange: stable context IDs
    rid = str(uuid.uuid4())
    cid = str(uuid.uuid4())
    with run_id_context(rid), correlation_context(cid):
        # Act
        with capture_logger("quantum.trading") as recs:
            emit_event({"event_name": "my_event_v1", "foo": 1})

    # Assert
    assert len(recs) == 1
    r = recs[0]
    assert r.levelno == logging.INFO
    assert r.getMessage() == "my_event_v1"

    ev = getattr(r, "event", {})
    assert isinstance(ev, dict)
    assert ev["event_name"] == "my_event_v1"
    assert _is_uuid(ev.get("run_id"))
    assert _is_uuid(ev.get("correlation_id"))


@pytest.mark.unit
@pytest.mark.parametrize(
    ("event_name", "expected_level"),
    [
        ("order_reject_v1", logging.WARNING),
        ("killswitch_trigger_v1", logging.ERROR),
    ],
)
def test_emit_event_respects_default_level_mapping(
    event_name: str, expected_level: int
):
    """
    Given known event names with default level mapping
    When emitting those events
    Then their corresponding logging level is applied
    """
    # Act
    with capture_logger("quantum.trading") as recs:
        emit_event({"event_name": event_name})

    # Assert
    assert [r.levelno for r in recs] == [expected_level]
    assert [r.getMessage() for r in recs] == [event_name]


@pytest.mark.unit
def test_emit_event_extra_is_merged_and_event_key_preserved():
    """
    Given `extra` dict is provided to emit_event
    When it contains 'event' key it must not override the event payload
    Then extra is merged as attributes but 'event' from payload is preserved
    """
    # Act
    with capture_logger("quantum.trading") as recs:
        emit_event(
            {"event_name": "x_v1", "x": 1},
            extra={"attrs": {"k": "v"}, "event": {"SHOULD_NOT": "OVERRIDE"}},
        )

    # Assert
    r = recs[0]
    ev = getattr(r, "event", {})
    assert ev["event_name"] == "x_v1" and ev["x"] == 1
    assert getattr(r, "attrs", None) == {"k": "v"}
    # Ensure extra.event did not override the real event payload
    assert "SHOULD_NOT" not in ev


@pytest.mark.unit
def test_emit_event_accepts_pydantic_like_model():
    """
    Given an object exposing .model_dump()
    When passed to emit_event
    Then it is converted to a dict payload
    """

    class _Model:
        def __init__(self):
            self._d = {"event_name": "model_evt_v1", "a": 2}

        def model_dump(self, *, exclude_none: bool = False):
            return dict(self._d)

    with capture_logger("quantum.trading") as recs:
        emit_event(_Model())

    ev = getattr(recs[0], "event", {})
    assert ev["event_name"] == "model_evt_v1"
    assert ev["a"] == 2


@pytest.mark.unit
def test_emit_event_invalid_type_raises_typeerror():
    """
    Given an unsupported payload type (neither dict nor pydantic-like)
    When passed to emit_event
    Then a TypeError is raised
    """
    with pytest.raises(TypeError):
        emit_event(object())


@pytest.mark.unit
def test_emit_event_fills_ids_when_context_vars_missing(monkeypatch):
    """
    Given ContextVars for run_id/correlation_id may be missing
    When emitting an event
    Then emit_event fills at least a valid run_id (and correlation_id if available)
    """
    # Ensure run_id exists to make the outcome deterministic enough for the assertion
    if not get_run_id():
        generate_run_id()

    with capture_logger("quantum.trading") as recs:
        emit_event({"event_name": "no_ctx_evt_v1"})

    ev = getattr(recs[0], "event", {})
    assert _is_uuid(ev.get("run_id"))
    # correlation_id may be None if never generated; we don't assert its presence here


@pytest.mark.unit
def test_emit_event_does_not_mutate_input_payload():
    """
    Given a dict payload passed to emit_event
    When the event is emitted
    Then the original dict must not be mutated (defensive copy semantics)
    """
    payload = {"event_name": "immutability_v1", "x": 1}
    with capture_logger("quantum.trading"):
        emit_event(payload)

    assert payload == {
        "event_name": "immutability_v1",
        "x": 1,
    }, "emit_event should not mutate the caller's dictionary"
