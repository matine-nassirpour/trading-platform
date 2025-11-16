import re
import uuid

from datetime import UTC, datetime

_SAFE = re.compile(r"^[A-Za-z0-9\-]+$")


def generate_audit_blob_name(
    now: datetime | None = None, unique_id: str | None = None, prefix: str | None = None
) -> str:
    dt = (now or datetime.now(UTC)).astimezone(UTC)
    ts = dt.strftime("%Y/%m/%d/%H%M%S")
    uid = unique_id or str(uuid.uuid4())
    if not _SAFE.match(uid):
        raise ValueError("unique_id contains unsafe characters")
    name = f"{ts}-{uid}.json"
    if prefix:
        if not _SAFE.match(prefix):
            raise ValueError("prefix contains unsafe characters")
        name = f"{ts}-{prefix}-{uid}.json"
    return name


def partition_path_components(dt: datetime) -> tuple[str, str, str, str]:
    """
    Returns ('YYYY', 'MM', 'DD', 'HH') for building partitioned directories.
    """
    dtu = dt.astimezone(UTC)
    return (
        dtu.strftime("%Y"),
        dtu.strftime("%m"),
        dtu.strftime("%d"),
        dtu.strftime("%H"),
    )
