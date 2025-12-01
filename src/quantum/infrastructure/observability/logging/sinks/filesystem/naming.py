import re
import uuid

from datetime import UTC, datetime
from typing import Final

_SAFE = re.compile(r"^[A-Za-z0-9\-]+$")
_EVENTS_PREFIX: Final[str] = "events"
_BAD_PREFIX: Final[str] = "bad-logs"
_EXT: Final[str] = ".jsonl"


def events_filename(yyyy: str, mm: str, dd: str, hh: str, part: int) -> str:
    suffix = f".part{part}" if part > 0 else ""
    return f"{_EVENTS_PREFIX}-{yyyy}{mm}{dd}-{hh}{suffix}{_EXT}"


def bad_filename(yyyy: str, mm: str, dd: str, hh: str, part: int) -> str:
    suffix = f".part{part}" if part > 0 else ""
    return f"{_BAD_PREFIX}-{yyyy}{mm}{dd}-{hh}{suffix}{_EXT}"


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
