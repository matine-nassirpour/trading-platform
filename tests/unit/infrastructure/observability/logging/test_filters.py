from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, cast

import pytest

from quantum.infrastructure.observability.logging.constants import get_audit_allowlist
from quantum.infrastructure.observability.logging.filters import (
    AuditEventFilter,
    IgnoreLibrariesFilter,
    InfoSamplerFilter,
    LoggingContextFilter,
    MonotonicTimestampFilter,
    RateLimitFilter,
    RedactFilter,
    StaticFieldsFilter,
)

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

_NumberLike = float | int | str | bytes


def _make_record(
    name: str = "t",
    level: int = logging.INFO,
    msg: str = "hello",
    *,
    extra: dict[str, Any] | None = None,
    exc_info: Any = None,
) -> logging.LogRecord:
    logger = logging.getLogger(name)
    rec = logger.makeRecord(
        name=name, level=level, fn="x.py", lno=123, msg=msg, args=(), exc_info=exc_info
    )
    if extra:
        for k, v in extra.items():
            setattr(rec, k, v)
    return rec


def _counter_value(c: Any) -> float:
    """
    Safe read of prometheus_client Counter (isolated registry via conftest fixture).
    """
    maybe_get = getattr(getattr(c, "_value", None), "get", None)
    if not callable(maybe_get):
        return -1.0
    try:
        return float(cast(Callable[[], _NumberLike], maybe_get)())
    except Exception:
        return -1.0


# ──────────────────────────────────────────────────────────────────────────────
# IgnoreLibrariesFilter / LoggingContextFilter / MonotonicTimestampFilter
# ──────────────────────────────────────────────────────────────────────────────


def test_ignore_libraries_filter_blocks_known_prefixes():
    f = IgnoreLibrariesFilter()
    blocked = [
        "urllib3.connectionpool",
        "requests.packages.urllib3.connectionpool",
        "opentelemetry.sdk._logs",
        "opentelemetry.sdk.trace",
        "opentelemetry.sdk.trace.export",
        "opentelemetry.sdk._shared_internal",
    ]
    for name in blocked:
        rec = _make_record(name=name)
        assert f.filter(rec) is False, f"should block {name}"

    # non bloqué
    rec2 = _make_record(name="my.app.component")
    assert f.filter(rec2) is True


def test_logging_context_filter_injects_env():
    f = LoggingContextFilter(env="prod")
    rec = _make_record(name="x")
    assert f.filter(rec) is True
    assert getattr(rec, "env") == "prod"


def test_monotonic_timestamp_filter_injects_once():
    f = MonotonicTimestampFilter()
    rec = _make_record()
    assert not hasattr(rec, "ts_monotonic_ms")
    assert f.filter(rec) is True
    first = rec.ts_monotonic_ms
    assert isinstance(first, int)

    # ne réécrit pas si déjà présent
    rec2 = _make_record(extra={"ts_monotonic_ms": 123})
    assert f.filter(rec2) is True
    assert rec2.ts_monotonic_ms == 123


# ──────────────────────────────────────────────────────────────────────────────
# AuditEventFilter
# ──────────────────────────────────────────────────────────────────────────────


def test_audit_event_filter_allowlist_and_suffix(monkeypatch):
    # Étend l'allowlist via l'env (CSV), sans suffixes (normalisation)
    monkeypatch.setenv("QUANTUM_AUDIT_EVENTS", "custom_evt_v1,order_fill_v2")
    monkeypatch.setenv("QUANTUM_AUDIT_EVENTS_VERSION", "v1")

    # sanity: set résultant inclut baseline + custom
    al = get_audit_allowlist("v1")
    assert "order_submit" in al  # baseline
    assert "order_fill" in al  # baseline (suffix retiré)
    assert "custom_evt" in al

    f = AuditEventFilter()

    # 1) non-dict → rejet
    rec = _make_record(extra={"event": "not a dict"})
    assert f.filter(rec) is False

    # 2) dict sans event_name → rejet
    rec2 = _make_record(extra={"event": {"foo": "bar"}})
    assert f.filter(rec2) is False

    # 3) event_name inconnu → rejet
    rec3 = _make_record(extra={"event": {"event_name": "unknown_evt"}})
    assert f.filter(rec3) is False

    # 4) suffix version _v2 accepté si base présent
    rec4 = _make_record(extra={"event": {"event_name": "order_fill_v2"}})
    assert f.filter(rec4) is True

    # 5) notre custom (avec suffixe v1) → accepté
    rec5 = _make_record(extra={"event": {"event_name": "custom_evt_v1"}})
    assert f.filter(rec5) is True


# ──────────────────────────────────────────────────────────────────────────────
# RedactFilter
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.usefixtures("no_rate_limit_no_sampling")
def test_redact_filter_attrs_and_msg_and_counter(monkeypatch):
    """
    - Redaction des clés sensibles dans attrs (→ compteur ++ si plus court)
    - Redaction JWT/HEX32 dans msg
    - Troncature longue chaîne msg (> MAX_VALUE_LEN)
    """
    from quantum.infrastructure.observability.metrics.health import (
        logging_redactions_total as red_counter,
    )

    before = _counter_value(red_counter)

    f = RedactFilter()

    # --- attrs secrets + long string (assure réduction mesurable) ---
    long_secret = "s" * (RedactFilter.MAX_VALUE_LEN + 100)
    attrs = {
        "password": "p@ss",  # pragma: allowlist secret
        "token": "abcd" * 20,
        "nested": {"client_secret": "xx", "ok": 1},  # pragma: allowlist secret
        "plain": "fine",
        "long": long_secret,
    }
    rec = _make_record(msg="no jwt yet", extra={"attrs": attrs})
    assert f.filter(rec) is True

    # secrets masqués + troncature appliquée
    red = rec.attrs
    assert red["password"] == "[REDACTED]"
    assert red["nested"]["client_secret"] == "[REDACTED]"
    assert isinstance(red["plain"], str) and red["plain"] == "fine"
    assert (
        red["long"].endswith("…") and len(red["long"]) == RedactFilter.MAX_VALUE_LEN + 1
    )

    after = _counter_value(red_counter)
    assert after == before + 1.0, "redactions counter should increment on attrs shrink"

    # --- msg: JWT-like + HEX32 + troncature ---
    jwt_like = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6Imp3dCIsImlhdCI6MTUxNjIzOTAyMn0."
        "TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ"  # pragma: allowlist secret
    )
    hex32 = "a" * 32
    very_long = "X" * (RedactFilter.MAX_VALUE_LEN + 500)

    rec2 = _make_record(msg=f"token={jwt_like} hex={hex32} long={very_long}")
    assert f.filter(rec2) is True
    # message nettoyé
    assert "[REDACTED]" in rec2.msg
    assert "token=" in rec2.msg and "hex=" in rec2.msg
    # troncature
    assert rec2.msg.endswith("…")
    assert len(rec2.msg) == RedactFilter.MAX_VALUE_LEN + 1


# ──────────────────────────────────────────────────────────────────────────────
# RateLimitFilter
# ──────────────────────────────────────────────────────────────────────────────


def test_rate_limit_filter_bucket_and_refill(monkeypatch):
    """
    max_per_sec=2 → 2 premières acceptées, 3e rejettée sans avance de temps.
    Puis +0.5s (toujours 3e rejetée), puis +1s (devient acceptée).
    On monkeypatch `time.monotonic` du module filters pour contrôler l'horloge.
    """
    import quantum.infrastructure.observability.logging.filters as fmod

    # horloge contrôlée
    t = [1000.0]

    def _mono():
        return t[0]

    monkeypatch.setattr(fmod.time, "monotonic", _mono, raising=True)

    rl = RateLimitFilter(max_per_sec=2.0)

    # Au départ, le seau contient 2 jetons (voir init)
    r1 = rl.filter(_make_record())
    r2 = rl.filter(_make_record())
    r3 = rl.filter(_make_record())
    assert r1 is True and r2 is True and r3 is False, "3e doit être rejetée sans refill"

    # avance +0.5s → refill = 1 jeton/s * 0.5 * 2 = 1.0 ? Non: rate=2/s → +1.0 jeton
    t[0] += 0.5
    r4 = rl.filter(_make_record())
    assert r4 is True  # consomme le jeton reconstitué
    r5 = rl.filter(_make_record())
    assert r5 is False

    # avance encore +1s → +2 jetons → 2 acceptées
    t[0] += 1.0
    r6 = rl.filter(_make_record())
    r7 = rl.filter(_make_record())
    r8 = rl.filter(_make_record())
    assert r6 is True and r7 is True and r8 is False


# ──────────────────────────────────────────────────────────────────────────────
# InfoSamplerFilter
# ──────────────────────────────────────────────────────────────────────────────


def test_info_sampler_filter_every_3():
    """
    sample_every=3 → 1er & 2e INFO droppés, 3e accepté, etc.
    Non-INFO toujours accepté.
    """
    s = InfoSamplerFilter(sample_every=3)

    # Non-INFO -> toujours True
    assert s.filter(_make_record(level=logging.WARNING)) is True

    # INFO: 1 → drop ; 2 → drop ; 3 → pass ; 4 → drop ; 5 → drop ; 6 → pass
    results = [s.filter(_make_record(level=logging.INFO)) for _ in range(6)]
    # on n'a que des INFO ci-dessus ; attendus: [False, False, True, False, False, True]
    assert results == [False, False, True, False, False, True]


# ──────────────────────────────────────────────────────────────────────────────
# StaticFieldsFilter
# ──────────────────────────────────────────────────────────────────────────────


def test_static_fields_filter_sets_and_does_not_overwrite():
    f = StaticFieldsFilter(
        service_name="svcA", service_namespace="nsA", service_version="1.0.0"
    )

    # injecte si absent
    rec = _make_record()
    assert f.filter(rec) is True
    assert rec.service_name == "svcA"
    assert rec.service_namespace == "nsA"
    assert rec.service_version == "1.0.0"

    # ne remplace pas si déjà présent
    rec2 = _make_record(
        extra={
            "service_name": "svcB",
            "service_namespace": "nsB",
            "service_version": "2.0.0",
        }
    )
    assert f.filter(rec2) is True
    assert rec2.service_name == "svcB"
    assert rec2.service_namespace == "nsB"
    assert rec2.service_version == "2.0.0"
