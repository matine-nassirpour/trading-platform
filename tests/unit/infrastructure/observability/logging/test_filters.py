from __future__ import annotations

import logging

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
from tests.support.factories import make_record
from tests.support.logging_utils import counter_value

# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ IgnoreLibrariesFilter / LoggingContextFilter / MonotonicTimestampFilter     │
# ╰─────────────────────────────────────────────────────────────────────────────╯


def test_ignore_libraries_filter_blocks_known_prefixes():
    """
    Given noisy library logger prefixes
    When passing records through IgnoreLibrariesFilter
    Then those records are dropped and others pass through
    """
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
        rec = make_record(name=name)
        assert f.filter(rec) is False, f"should block {name}"

    # Non-blocked prefix should pass
    rec2 = make_record(name="my.app.component")
    assert f.filter(rec2) is True


def test_logging_context_filter_injects_env():
    """
    Given a LoggingContextFilter configured with env='prod'
    When a record passes through
    Then 'env' is injected (unless already present)
    """
    f = LoggingContextFilter(env="prod")
    rec = make_record(name="x")
    assert f.filter(rec) is True
    assert getattr(rec, "env") == "prod"


def test_monotonic_timestamp_filter_injects_once():
    """
    Given a record without ts_monotonic_ms
    When it passes through MonotonicTimestampFilter
    Then the field is injected exactly once and not overwritten if already present
    """
    f = MonotonicTimestampFilter()
    rec = make_record()
    assert not hasattr(rec, "ts_monotonic_ms")
    assert f.filter(rec) is True
    first = getattr(rec, "ts_monotonic_ms")
    assert isinstance(first, int)

    # Do not rewrite if already present
    rec2 = make_record(extra={"ts_monotonic_ms": 123})
    assert f.filter(rec2) is True
    assert getattr(rec2, "ts_monotonic_ms") == 123


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ AuditEventFilter                                                            │
# ╰─────────────────────────────────────────────────────────────────────────────╯


def test_audit_event_filter_allowlist_and_suffix(monkeypatch):
    """
    Given QUANTUM_AUDIT_EVENTS extends the allowlist
    When AuditEventFilter evaluates various payloads
    Then only dicts with an allowed event_name (version-agnostic) pass
    """
    # Extend the allowlist via environment (CSV), version suffix normalization
    monkeypatch.setenv("QUANTUM_AUDIT_EVENTS", "custom_evt_v1,order_fill_v2")
    monkeypatch.setenv("QUANTUM_AUDIT_EVENTS_VERSION", "v1")

    # Sanity: resulting set includes baseline + custom
    al = get_audit_allowlist("v1")
    assert "order_submit" in al  # baseline
    assert "order_fill" in al  # baseline (suffix stripped)
    assert "custom_evt" in al

    f = AuditEventFilter()

    # 1) non-dict → reject
    rec = make_record(extra={"event": "not a dict"})
    assert f.filter(rec) is False

    # 2) dict without event_name → reject
    rec2 = make_record(extra={"event": {"foo": "bar"}})
    assert f.filter(rec2) is False

    # 3) unknown event_name → reject
    rec3 = make_record(extra={"event": {"event_name": "unknown_evt"}})
    assert f.filter(rec3) is False

    # 4) version suffix accepted if base present
    rec4 = make_record(extra={"event": {"event_name": "order_fill_v2"}})
    assert f.filter(rec4) is True

    # 5) our custom (with suffix v1) → accepted
    rec5 = make_record(extra={"event": {"event_name": "custom_evt_v1"}})
    assert f.filter(rec5) is True


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ RedactFilter                                                                │
# ╰─────────────────────────────────────────────────────────────────────────────╯


@pytest.mark.usefixtures("no_rate_limit_no_sampling")
def test_redact_filter_attrs_and_msg_and_counter(monkeypatch):
    """
    Given sensitive keys in attrs and secrets in msg (JWT/HEX)
    When passing through RedactFilter
    Then sensitive values are redacted, long strings are truncated,
         and a redaction counter is incremented when shrink occurs
    """
    from quantum.infrastructure.observability.metrics.health import (
        logging_redactions_total as red_counter,
    )

    before = counter_value(red_counter)

    f = RedactFilter()

    # --- attrs secrets + long string (ensure measurable reduction) ---
    long_secret = "s" * (RedactFilter.MAX_VALUE_LEN + 100)
    attrs = {
        "password": "p@ss",  # pragma: allowlist secret
        "token": "abcd" * 20,
        "nested": {"client_secret": "xx", "ok": 1},  # pragma: allowlist secret
        "plain": "fine",
        "long": long_secret,
    }
    rec = make_record(msg="no jwt yet", extra={"attrs": attrs})
    assert f.filter(rec) is True

    # Secrets redacted + truncation applied
    red = getattr(rec, "attrs")
    assert red["password"] == "[REDACTED]"
    assert red["nested"]["client_secret"] == "[REDACTED]"
    assert isinstance(red["plain"], str) and red["plain"] == "fine"
    assert (
        red["long"].endswith("…") and len(red["long"]) == RedactFilter.MAX_VALUE_LEN + 1
    )

    after = counter_value(red_counter)
    assert after == before + 1.0, "redactions counter should increment on attrs shrink"

    # --- msg: JWT-like + HEX32 + truncation ---
    jwt_like = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6Imp3dCIsImlhdCI6MTUxNjIzOTAyMn0."
        "TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ"  # pragma: allowlist secret
    )
    hex32 = "a" * 32
    very_long = "X" * (RedactFilter.MAX_VALUE_LEN + 500)

    rec2 = make_record(msg=f"token={jwt_like} hex={hex32} long={very_long}")
    assert f.filter(rec2) is True
    # message cleaned
    assert "[REDACTED]" in rec2.msg
    assert "token=" in rec2.msg and "hex=" in rec2.msg
    # truncation
    assert rec2.msg.endswith("…")
    assert len(rec2.msg) == RedactFilter.MAX_VALUE_LEN + 1


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ RateLimitFilter                                                             │
# ╰─────────────────────────────────────────────────────────────────────────────╯


def test_rate_limit_filter_bucket_and_refill(monkeypatch):
    """
    Given max_per_sec=2
    When consuming tokens without advancing time
    Then the 3rd INFO is dropped
    And after +0.5s exactly one token is refilled (with rate=2/s)
    And after +1.0s two more tokens are available
    """
    import quantum.infrastructure.observability.logging.filters as fmod

    # Controlled monotonic clock
    t = [1000.0]

    def _mono():
        return t[0]

    monkeypatch.setattr(fmod.time, "monotonic", _mono, raising=True)

    rl = RateLimitFilter(max_per_sec=2.0)

    # Initially, bucket holds 2 tokens (per init)
    r1 = rl.filter(make_record())
    r2 = rl.filter(make_record())
    r3 = rl.filter(make_record())
    assert (
        r1 is True and r2 is True and r3 is False
    ), "3rd must be dropped without refill"

    # +0.5s → refill = 2/s * 0.5 = +1 token
    t[0] += 0.5
    r4 = rl.filter(make_record())
    assert r4 is True  # consumes the refilled token
    r5 = rl.filter(make_record())
    assert r5 is False

    # +1.0s → +2 tokens → 2 accepted, 3rd dropped
    t[0] += 1.0
    r6 = rl.filter(make_record())
    r7 = rl.filter(make_record())
    r8 = rl.filter(make_record())
    assert r6 is True and r7 is True and r8 is False


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ InfoSamplerFilter                                                           │
# ╰─────────────────────────────────────────────────────────────────────────────╯


def test_info_sampler_filter_every_3():
    """
    Given sample_every=3
    When sending INFO logs
    Then the 1st & 2nd are dropped, the 3rd is accepted, and so on
    Non-INFO levels always pass
    """
    s = InfoSamplerFilter(sample_every=3)

    # Non-INFO → always True
    assert s.filter(make_record(level=logging.WARNING)) is True

    # INFO: 1 → drop ; 2 → drop ; 3 → pass ; 4 → drop ; 5 → drop ; 6 → pass
    results = [s.filter(make_record(level=logging.INFO)) for _ in range(6)]
    assert results == [False, False, True, False, False, True]


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ StaticFieldsFilter                                                          │
# ╰─────────────────────────────────────────────────────────────────────────────╯


def test_static_fields_filter_sets_and_does_not_overwrite():
    """
    Given StaticFieldsFilter(service_name/namespace/version)
    When a record passes with/without existing fields
    Then fields are injected when missing and never overwritten if present
    """
    f = StaticFieldsFilter(
        service_name="svcA", service_namespace="nsA", service_version="1.0.0"
    )

    # Inject when absent
    rec = make_record()
    assert f.filter(rec) is True
    assert getattr(rec, "service_name") == "svcA"
    assert getattr(rec, "service_namespace") == "nsA"
    assert getattr(rec, "service_version") == "1.0.0"

    # Do not replace when already present
    rec2 = make_record(
        extra={
            "service_name": "svcB",
            "service_namespace": "nsB",
            "service_version": "2.0.0",
        }
    )
    assert f.filter(rec2) is True
    assert getattr(rec2, "service_name") == "svcB"
    assert getattr(rec2, "service_namespace") == "nsB"
    assert getattr(rec2, "service_version") == "2.0.0"
