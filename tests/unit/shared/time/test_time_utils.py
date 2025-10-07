from __future__ import annotations

from datetime import datetime, timezone

from quantum.shared.time import naming as nm
from quantum.shared.time import rfc3339 as rfc


def test_from_unix_s_to_rfc3339_ms_and_to_rfc3339_ms_roundtrip():
    # 2025-10-07 12:34:56.789 UTC
    ts = 1760147696.789
    s = rfc.from_unix_s_to_rfc3339_ms(ts)
    assert s.endswith("Z")
    # parse et compare à ±1ms
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    assert abs(dt.timestamp() - ts) < 0.001

    # to_rfc3339_ms pour naive/aware
    naive = datetime(2025, 10, 7, 12, 34, 56, 789000)  # naive → traité comme UTC
    aware = datetime(2025, 10, 7, 12, 34, 56, 789000, tzinfo=timezone.utc)
    assert rfc.to_rfc3339_ms(naive) == "2025-10-07T12:34:56.789Z"
    assert rfc.to_rfc3339_ms(aware) == "2025-10-07T12:34:56.789Z"


def test_now_rfc3339_ms_format_and_monotonic_elapsed():
    s = rfc.now_rfc3339_ms()
    # Format simple: contient 'T' et se termine par Z, avec millisecondes
    assert "T" in s and s.endswith("Z")
    # monotonic
    start = rfc.now_mono_ms()
    e = rfc.elapsed_ms(start)
    assert isinstance(e, int) and e >= 0


def test_partition_and_generate_audit_blob_name_happy_path_and_validation():
    dt = datetime(2025, 10, 7, 15, 16, 17, tzinfo=timezone.utc)
    y, m, d, h = nm.partition_path_components(dt)
    assert (y, m, d, h) == ("2025", "10", "07", "15")

    name = nm.generate_audit_blob_name(now=dt, unique_id="abc123", prefix="trade")
    # "YYYY/MM/DD/HHMMSS-prefix-uid.json"
    assert name.startswith("2025/10/07/151617-trade-abc123")
    assert name.endswith(".json")

    # sans prefix
    name2 = nm.generate_audit_blob_name(now=dt, unique_id="abc123")
    assert name2.startswith("2025/10/07/151617-abc123")

    # validations
    try:
        nm.generate_audit_blob_name(now=dt, unique_id="bad*uid")
        assert False, "expected ValueError for bad unique_id"
    except ValueError:
        pass
    try:
        nm.generate_audit_blob_name(now=dt, unique_id="abc", prefix="bad/prefix")
        assert False, "expected ValueError for bad prefix"
    except ValueError:
        pass
