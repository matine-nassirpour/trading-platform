from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Any, cast

import pytest

from quantum.infrastructure.observability.logging.formatter import JsonFormatter

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

_NumberLike = float | int | str | bytes
formatter = JsonFormatter()


def _make_record(
    name: str = "t",
    level: int = logging.INFO,
    msg: str = "hello",
    *,
    extra: dict[str, Any] | None = None,
    exc_info: Any = None,
) -> logging.LogRecord:
    """
    Utility to create a LogRecord with optional extras/exc_info.
    """
    logger = logging.getLogger(name)
    rec = logger.makeRecord(
        name=name, level=level, fn="x.py", lno=123, msg=msg, args=(), exc_info=exc_info
    )
    if extra:
        for k, v in extra.items():
            setattr(rec, k, v)
    return rec


def _parse(formatted: str) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(formatted))


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
# Tests
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.usefixtures("no_rate_limit_no_sampling")
class TestFormatterOTelContext:
    def test_valid_trace_context_with_bool_sampled(self, monkeypatch):
        """
        Contexte OTel valide → trace_id/span_id hex fixés + sampled=True
        (variant: TraceFlags.sampled bool).
        """

        class _SpanContext:
            is_valid = True
            trace_id = int("f" * 32, 16)
            span_id = int("a" * 16, 16)

            class _Flags:
                sampled = True  # bool attribute variant

            trace_flags = _Flags()

        class _Span:
            @staticmethod
            def get_span_context():
                return _SpanContext()

        monkeypatch.setattr(
            "quantum.infrastructure.observability.logging.formatter.get_current_span",
            lambda: _Span(),
            raising=True,
        )

        rec = _make_record(
            extra={
                "env": "dev",
                "service_name": "svc",
                "service_version": "1",
                "service_namespace": "ns",
            }
        )
        js = _parse(formatter.format(rec))

        assert js["trace_id"] == "f" * 32
        assert js["span_id"] == "a" * 16
        assert js.get("sampled") is True

    def test_invalid_or_absent_context_returns_none(self, monkeypatch):
        """
        Contexte invalide → (trace_id, span_id, sampled) absents.
        """

        class _BadCtx:
            is_valid = False

        class _SpanBad:
            @staticmethod
            def get_span_context():
                return _BadCtx()

        monkeypatch.setattr(
            "quantum.infrastructure.observability.logging.formatter.get_current_span",
            lambda: _SpanBad(),
            raising=True,
        )
        rec = _make_record(extra={"env": "dev"})
        js = _parse(formatter.format(rec))
        assert js.get("trace_id") is None
        assert js.get("span_id") is None
        assert js.get("sampled") is None

    def test_sampled_callable_and_bitmask_variants(self, monkeypatch):
        """
        TraceFlags.sampled() (callable) et int bitmask (0x01) → sampled=True
        """

        # Variant 1: callable sampled()
        class _FlagsCallable:
            @staticmethod
            def sampled() -> bool:
                return True

        class _CtxCallable:
            is_valid = True
            trace_id = 1
            span_id = 2
            trace_flags = _FlagsCallable()

        class _SpanCallable:
            @staticmethod
            def get_span_context():
                return _CtxCallable()

        monkeypatch.setattr(
            "quantum.infrastructure.observability.logging.formatter.get_current_span",
            lambda: _SpanCallable(),
            raising=True,
        )
        js1 = _parse(formatter.format(_make_record(extra={"env": "dev"})))
        assert js1.get("sampled") is True

        # Variant 2: int mask
        class _CtxMask:
            is_valid = True
            trace_id = 3
            span_id = 4
            trace_flags = 0x01  # low bit set

        class _SpanMask:
            @staticmethod
            def get_span_context():
                return _CtxMask()

        monkeypatch.setattr(
            "quantum.infrastructure.observability.logging.formatter.get_current_span",
            lambda: _SpanMask(),
            raising=True,
        )
        js2 = _parse(formatter.format(_make_record(extra={"env": "dev"})))
        assert js2.get("sampled") is True


@pytest.mark.usefixtures("no_rate_limit_no_sampling")
class TestFormatterExceptions:
    def test_structured_and_legacy_exception_fields_present(self):
        """
        exc_info → exception_type, exception_message, exception_stacktrace,
        + champ legacy 'exception' (texte).
        """
        try:
            raise ValueError("boom")
        except ValueError as e:
            rec = _make_record(
                level=logging.ERROR,
                msg="with exc",
                exc_info=(e.__class__, e, e.__traceback__),
                extra={"env": "dev"},
            )

        js = _parse(formatter.format(rec))
        assert js["level"] == "ERROR"
        # Structuré
        assert js.get("exception_type") == "ValueError"
        assert js.get("exception_message") == "boom"
        assert (
            isinstance(js.get("exception_stacktrace"), str)
            and "ValueError" in js["exception_stacktrace"]
        )
        # Legacy court
        assert isinstance(js.get("exception"), str) and "ValueError" in js["exception"]


@pytest.mark.usefixtures("no_rate_limit_no_sampling")
class TestFormatterFallbackAndMetrics:
    def test_pydantic_validation_error_fallback_and_counter_increment(
        self, monkeypatch
    ):
        """
        Injecte une correlation_id invalide via monkeypatch → Pydantic lève,
        le formatter produit un payload de fallback + incrémente
        logging_schema_validation_errors_total.
        """
        # Counter initial
        from quantum.infrastructure.observability.metrics.health import (
            logging_schema_validation_errors_total as counter,
        )

        before = _counter_value(counter)

        # Monkeypatch: get_correlation_id retourne une string non-UUID
        monkeypatch.setattr(
            "quantum.infrastructure.observability.logging.formatter.get_correlation_id",
            lambda: "not-a-uuid",
            raising=True,
        )

        rec = _make_record(level=logging.INFO, msg="bad corr id", extra={"env": "dev"})
        js = _parse(formatter.format(rec))

        # Fallback détectable
        assert js.get("log_schema_version") == "fallback"
        assert isinstance(js.get("validation_error"), str) and js["validation_error"]

        # Compteur ++
        after = _counter_value(counter)
        assert after >= 0.0 and after == before + 1.0


@pytest.mark.usefixtures("no_rate_limit_no_sampling")
class TestFormatterAttrsAndExclusions:
    def test_attrs_sanitize_and_std_exclusions(self):
        """
        - bytes → repr tronqué
        - set/tuple → list
        - long string → troncature + '…'
        - exclusions des champs standard et des resource fields déjà top-level
        """
        big = "A" * 11_000  # > 10_000 (limite formatter)
        extra = {
            "env": "dev",  # top-level via overrides
            "service_name": "svc",
            "service_version": "1.2.3",
            "service_namespace": "ns",
            "attrs": {
                "data_bytes": b"\x00\x01\x02" * 64,  # long bytes
                "a_set": {1, 2, 3},
                "a_tuple": (4, 5),
                "big": big,
                "nested": {"k": {6, 7}},
            },
            # champs standards qui ne doivent pas se retrouver dans attrs
            "lineno": 999,
            "module": "m",
        }
        rec = _make_record(level=logging.INFO, msg="sanitize", extra=extra)
        js = _parse(formatter.format(rec))

        # Top-level service & env
        assert js["env"] == "dev"
        assert js["service_name"] == "svc"
        assert js["service_version"] == "1.2.3"
        assert js["service_namespace"] == "ns"

        attrs = js.get("attrs", {})
        assert isinstance(attrs, dict)

        # bytes → repr (contient "… (truncated)" car >64)
        assert isinstance(attrs["data_bytes"], str)
        assert "truncated" in attrs["data_bytes"].lower()

        # set/tuple → list
        assert sorted(attrs["a_set"]) == [1, 2, 3]
        assert list(attrs["a_tuple"]) == [4, 5]

        # long string → troncature + ellipsis unicode
        assert isinstance(attrs["big"], str)
        assert attrs["big"].endswith("…")
        assert len(attrs["big"]) == 10_000 + 1  # tronqué + ellipsis

        # nested set → list
        assert sorted(attrs["nested"]["k"]) == [6, 7]

        # Exclusions: les champs standards ne doivent pas migrer dans attrs
        assert "lineno" not in attrs
        assert "module" not in attrs

    def test_exception_key_in_attrs_is_renamed(self):
        """
        Si 'exception' est passé en extra (top-level), il est remappé vers
        attrs.exception_obj pour éviter d'entrer en collision avec le champ
        legacy top-level 'exception' (string).
        """
        rec = _make_record(
            msg="collision",
            extra={
                "env": "dev",
                # <-- top-level, pas dans attrs
                "exception": {"kind": "ValueError", "msg": "x"},
            },
        )
        js = _parse(formatter.format(rec))

        # Dans ce scénario sans exc_info, le champ legacy top-level 'exception'
        # n'est pas renseigné (excluded si None).
        assert "exception" not in js or js.get("exception") is None

        # Notre payload a bien été remappé en attrs.exception_obj
        assert js["attrs"].get("exception_obj") == {"kind": "ValueError", "msg": "x"}


@pytest.mark.usefixtures("no_rate_limit_no_sampling")
class TestFormatterSeveritiesAndTimestamps:
    def test_severity_mapping_and_numbers_and_timestamps(self):
        """
        Vérifie:
        - mapping WARNING→WARN, CRITICAL→FATAL
        - severity_number borné [1..24]
        - timestamps présents (RFC3339 ms + unix_ms + monotonic_ms)
        """
        # WARNING → WARN
        js_warn = _parse(
            formatter.format(_make_record(level=logging.WARNING, extra={"env": "dev"}))
        )
        assert js_warn["level"] == "WARN"
        assert isinstance(js_warn.get("severity_number"), int)
        assert 1 <= js_warn["severity_number"] <= 24

        # CRITICAL → FATAL
        js_fatal = _parse(
            formatter.format(_make_record(level=logging.CRITICAL, extra={"env": "dev"}))
        )
        assert js_fatal["level"] == "FATAL"
        assert isinstance(js_fatal.get("severity_number"), int)
        assert 1 <= js_fatal["severity_number"] <= 24

        # Horodatage: RFC3339 ms, unix_ms, monotonic_ms
        base = _parse(
            formatter.format(_make_record(level=logging.INFO, extra={"env": "dev"}))
        )
        assert isinstance(base.get("timestamp"), str) and "T" in base["timestamp"]
        assert isinstance(base.get("ts_unix_ms"), int)
        assert isinstance(base.get("ts_monotonic_ms"), int)
