from __future__ import annotations

import logging
import uuid
from contextlib import contextmanager

import pytest

from quantum.infrastructure.observability.logging.event_emitter import emit_event
from quantum.shared.context.run_id import generate_run_id, get_run_id, run_id_context
from quantum.shared.correlation.correlation_id import correlation_context

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


class _ListHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super().__init__(level)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


@contextmanager
def _capture_logger(name: str, level: int = logging.DEBUG):
    lg = logging.getLogger(name)
    h = _ListHandler(level=level)
    old_level = lg.level
    lg.addHandler(h)
    lg.setLevel(min(old_level or level, level))
    try:
        yield h.records
    finally:
        lg.removeHandler(h)
        lg.setLevel(old_level)


def _is_uuid(s: str | None) -> bool:
    if not s:
        return False
    try:
        uuid.UUID(s)
        return True
    except Exception:
        return False


# ──────────────────────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────────────────────


def test_emit_event_injects_ids_and_uses_default_level_info(monkeypatch):
    """
    - Si run_id / correlation_id absents dans le payload → injectés depuis ContextVars.
    - Niveau par défaut: INFO (pour un event non mappé).
    """
    # contexte stable
    rid_cm = run_id_context(str(uuid.uuid4()))
    cid_cm = correlation_context(str(uuid.uuid4()))
    rid_cm.__enter__()
    cid_cm.__enter__()
    try:
        with _capture_logger("quantum.trading") as recs:
            emit_event({"event_name": "my_event_v1", "foo": 1})
        assert len(recs) == 1
        r = recs[0]
        assert r.levelno == logging.INFO
        assert r.getMessage() == "my_event_v1"
        ev = getattr(r, "event", {})
        assert isinstance(ev, dict)
        assert ev["event_name"] == "my_event_v1"
        # IDs injectés
        assert _is_uuid(ev.get("run_id"))
        assert _is_uuid(ev.get("correlation_id"))
    finally:
        cid_cm.__exit__(None, None, None)
        rid_cm.__exit__(None, None, None)


def test_emit_event_respects_default_level_mapping():
    """
    - order_reject_v1 → WARNING
    - killswitch_trigger_v1 → ERROR
    """
    with _capture_logger("quantum.trading") as recs:
        emit_event({"event_name": "order_reject_v1"})
        emit_event({"event_name": "killswitch_trigger_v1"})
    # Deux records
    assert [r.levelno for r in recs] == [logging.WARNING, logging.ERROR]
    assert [r.getMessage() for r in recs] == [
        "order_reject_v1",
        "killswitch_trigger_v1",
    ]


def test_emit_event_extra_is_merged_and_event_key_preserved():
    """
    - `extra` fusionné mais ne doit pas écraser "event" (réservé).
    """
    with _capture_logger("quantum.trading") as recs:
        emit_event(
            {"event_name": "x_v1", "x": 1},
            extra={"attrs": {"k": "v"}, "event": {"SHOULD_NOT": "OVERRIDE"}},
        )
    r = recs[0]
    ev = getattr(r, "event", {})
    assert ev["event_name"] == "x_v1" and ev["x"] == 1
    # extra fusionné
    assert getattr(r, "attrs", None) == {"k": "v"}
    # pas d’écrasement
    assert "SHOULD_NOT" not in ev


def test_emit_event_accepts_pydantic_like_model():
    """
    Accepte un objet ayant `.model_dump()` → converti en dict.
    """

    class _Model:
        def __init__(self):
            self._d = {"event_name": "model_evt_v1", "a": 2}

        def model_dump(self, exclude_none: bool = False):
            return dict(self._d)

    with _capture_logger("quantum.trading") as recs:
        emit_event(_Model())
    ev = getattr(recs[0], "event", {})
    assert ev["event_name"] == "model_evt_v1"
    assert ev["a"] == 2


def test_emit_event_invalid_type_raises_typeerror():
    with pytest.raises(TypeError):
        emit_event(object())  # ni pydantic-like ni dict


def test_emit_event_fills_ids_when_context_vars_missing(monkeypatch):
    """
    Même sans ContextVars pré-positionnés, emit_event alimente run_id/correlation_id
    (setdefault avec get_run_id/get_correlation_id → run_id peut être None si jamais
    généré, donc on force un run_id pour un résultat stable).
    """
    # Reset: pas de run_id dans le contexte
    # (aucune API "reset" publique, on génère au moins un run_id pour assurer présence)
    if not get_run_id():
        generate_run_id()

    with _capture_logger("quantum.trading") as recs:
        emit_event({"event_name": "no_ctx_evt_v1"})
    ev = getattr(recs[0], "event", {})
    # au minimum run_id doit être présent & valide
    assert _is_uuid(ev.get("run_id"))
    # correlation_id peut être None si non créé — on n’impose pas sa présence ici
