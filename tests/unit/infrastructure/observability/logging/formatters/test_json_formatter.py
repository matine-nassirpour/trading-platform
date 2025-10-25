from __future__ import annotations

import json
import logging
from typing import Any, cast

import pytest

from quantum.infrastructure.observability.logging.formatters.json_formatter import (
    JsonFormatter,
)
from tests.support.factories import make_record
from tests.support.logging_utils import counter_value

# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Helpers                                                                     │
# ╰─────────────────────────────────────────────────────────────────────────────╯

formatter = JsonFormatter()


def _parse(formatted: str) -> dict[str, Any]:
    """Parse a JSON-formatted string into a dict with a precise type."""
    return cast(dict[str, Any], json.loads(formatted))


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Tests                                                                       │
# ╰─────────────────────────────────────────────────────────────────────────────╯


@pytest.mark.usefixtures("no_rate_limit_no_sampling")
class TestFormatterOTelContext:
    def test_valid_trace_context_with_bool_sampled(self, monkeypatch):
        """
        Given a valid OTel span context with boolean 'sampled'
        When formatting a record
        Then trace_id/span_id are emitted as hex strings and sampled=True
        """

        class _SpanContext:
            is_valid = True
            trace_id = int("f" * 32, 16)
            span_id = int("a" * 16, 16)

            class _Flags:
                sampled = True  # boolean attribute variant

            trace_flags = _Flags()

        class _Span:
            @staticmethod
            def get_span_context():
                return _SpanContext()

        monkeypatch.setattr(
            "quantum.infrastructure.observability.logging.formatters.json_formatter.get_current_span",
            lambda: _Span(),
            raising=True,
        )

        rec = make_record(
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
        Given an invalid or absent OTel span context
        When formatting a record
        Then trace_id/span_id/sampled are omitted (None)
        """

        class _BadCtx:
            is_valid = False

        class _SpanBad:
            @staticmethod
            def get_span_context():
                return _BadCtx()

        monkeypatch.setattr(
            "quantum.infrastructure.observability.logging.formatters.json_formatter.get_current_span",
            lambda: _SpanBad(),
            raising=True,
        )
        rec = make_record(extra={"env": "dev"})
        js = _parse(formatter.format(rec))
        assert js.get("trace_id") is None
        assert js.get("span_id") is None
        assert js.get("sampled") is None

    def test_sampled_callable_and_bitmask_variants(self, monkeypatch):
        """
        Given span contexts with TraceFlags.sampled() callable and bitmask int
        When formatting
        Then sampled=True is correctly derived in both cases
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
            "quantum.infrastructure.observability.logging.formatters.json_formatter.get_current_span",
            lambda: _SpanCallable(),
            raising=True,
        )
        js1 = _parse(formatter.format(make_record(extra={"env": "dev"})))
        assert js1.get("sampled") is True

        # Variant 2: int mask (low bit set)
        class _CtxMask:
            is_valid = True
            trace_id = 3
            span_id = 4
            trace_flags = 0x01

        class _SpanMask:
            @staticmethod
            def get_span_context():
                return _CtxMask()

        monkeypatch.setattr(
            "quantum.infrastructure.observability.logging.formatters.json_formatter.get_current_span",
            lambda: _SpanMask(),
            raising=True,
        )
        js2 = _parse(formatter.format(make_record(extra={"env": "dev"})))
        assert js2.get("sampled") is True


@pytest.mark.usefixtures("no_rate_limit_no_sampling")
class TestFormatterExceptions:
    def test_structured_and_legacy_exception_fields_present(self):
        """
        Given exc_info is provided
        When formatting
        Then structured exception fields and legacy 'exception' string are present
        """
        try:
            raise ValueError("boom")
        except ValueError as e:
            rec = make_record(
                level=logging.ERROR,
                msg="with exc",
                exc_info=(e.__class__, e, e.__traceback__),
                extra={"env": "dev"},
            )

        js = _parse(formatter.format(rec))
        assert js["level"] == "ERROR"
        # Structured
        assert js.get("exception_type") == "ValueError"
        assert js.get("exception_message") == "boom"
        assert (
            isinstance(js.get("exception_stacktrace"), str)
            and "ValueError" in js["exception_stacktrace"]
        )
        # Legacy short string
        assert isinstance(js.get("exception"), str) and "ValueError" in js["exception"]


@pytest.mark.usefixtures("no_rate_limit_no_sampling")
class TestFormatterFallbackAndMetrics:
    def test_pydantic_validation_error_fallback_and_counter_increment(
        self, monkeypatch
    ):
        """
        Given a formatter validation error (e.g., invalid correlation_id)
        When formatting
        Then a fallback payload is produced and the validation error counter increments
        """
        from quantum.infrastructure.observability.metrics.collectors.health_collector import (
            logging_schema_validation_errors_total as counter,
        )

        before = counter_value(counter)

        # Monkeypatch: get_correlation_id returns a non-UUID string
        monkeypatch.setattr(
            "quantum.infrastructure.observability.logging.formatters.json_formatter.get_correlation_id",
            lambda: "not-a-uuid",
            raising=True,
        )

        rec = make_record(level=logging.INFO, msg="bad corr id", extra={"env": "dev"})
        js = _parse(formatter.format(rec))

        # Fallback payload
        assert js.get("log_schema_version") == "fallback"
        assert isinstance(js.get("validation_error"), str) and js["validation_error"]

        after = counter_value(counter)
        assert after >= 0.0 and after == before + 1.0


@pytest.mark.usefixtures("no_rate_limit_no_sampling")
class TestFormatterAttrsAndExclusions:
    def test_attrs_sanitize_and_std_exclusions(self):
        """
        Given extra attrs containing bytes/set/tuple and long strings
        When formatting
        Then attrs are sanitized (bytes repr truncated, sets/tuples → lists, long strings truncated)
             and standard fields are not leaked into attrs
        """
        big = "A" * 11_000  # > 10_000 (formatter limit)
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
            # standard fields that must not end up under attrs
            "lineno": 999,
            "module": "m",
        }
        rec = make_record(level=logging.INFO, msg="sanitize", extra=extra)
        js = _parse(formatter.format(rec))

        # Top-level resource/ctx
        assert js["env"] == "dev"
        assert js["service_name"] == "svc"
        assert js["service_version"] == "1.2.3"
        assert js["service_namespace"] == "ns"

        attrs = js.get("attrs", {})
        assert isinstance(attrs, dict)

        # bytes → repr (contains "… (truncated)" since >64)
        assert isinstance(attrs["data_bytes"], str)
        assert "truncated" in attrs["data_bytes"].lower()

        # set/tuple → list
        assert sorted(attrs["a_set"]) == [1, 2, 3]
        assert list(attrs["a_tuple"]) == [4, 5]

        # long string → truncation + unicode ellipsis
        assert isinstance(attrs["big"], str)
        assert attrs["big"].endswith("…")
        assert len(attrs["big"]) == 10_000 + 1  # truncated + ellipsis

        # nested set → list
        assert sorted(attrs["nested"]["k"]) == [6, 7]

        # Exclusions: standard fields must not migrate into attrs
        assert "lineno" not in attrs
        assert "module" not in attrs

    def test_exception_key_in_attrs_is_renamed(self):
        """
        Given 'exception' key is provided at top-level extra
        When formatting
        Then it is remapped into attrs.exception_obj to avoid collision with legacy 'exception'
        """
        rec = make_record(
            msg="collision",
            extra={
                "env": "dev",
                # top-level in extra, not in attrs
                "exception": {"kind": "ValueError", "msg": "x"},
            },
        )
        js = _parse(formatter.format(rec))

        # In this scenario without exc_info, the legacy top-level 'exception' is omitted
        assert "exception" not in js or js.get("exception") is None

        # Our payload is remapped into attrs.exception_obj
        assert js["attrs"].get("exception_obj") == {"kind": "ValueError", "msg": "x"}


@pytest.mark.usefixtures("no_rate_limit_no_sampling")
class TestFormatterSeveritiesAndTimestamps:
    def test_severity_mapping_and_numbers_and_timestamps(self):
        """
        Given records at various Python logging levels
        When formatting
        Then OTel level mapping/name/number are correct
             and timestamps fields are present (RFC3339 ms, unix_ms, monotonic_ms)
        """
        # WARNING → WARN and 1..24 severity_number bound
        js_warn = _parse(
            formatter.format(make_record(level=logging.WARNING, extra={"env": "dev"}))
        )
        assert js_warn["level"] == "WARN"
        assert isinstance(js_warn.get("severity_number"), int)
        assert 1 <= js_warn["severity_number"] <= 24

        # CRITICAL → FATAL
        js_fatal = _parse(
            formatter.format(make_record(level=logging.CRITICAL, extra={"env": "dev"}))
        )
        assert js_fatal["level"] == "FATAL"
        assert isinstance(js_fatal.get("severity_number"), int)
        assert 1 <= js_fatal["severity_number"] <= 24

        # Timestamps: RFC3339 ms, unix_ms, monotonic_ms
        base = _parse(
            formatter.format(make_record(level=logging.INFO, extra={"env": "dev"}))
        )
        assert isinstance(base.get("timestamp"), str) and "T" in base["timestamp"]
        assert isinstance(base.get("ts_unix_ms"), int)
        assert isinstance(base.get("ts_monotonic_ms"), int)
