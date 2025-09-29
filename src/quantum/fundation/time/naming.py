import uuid
from datetime import datetime, timezone


def generate_audit_blob_name(
    now: datetime | None = None, unique_id: str | None = None
) -> str:
    """
    Returns 'YYYY/MM/DD/HHMMSS-UUID.json' in UTC.
    """
    dt = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    ts = dt.strftime("%Y/%m/%d/%H%M%S")
    uid = unique_id or str(uuid.uuid4())
    return f"{ts}-{uid}.json"


def partition_path_components(dt: datetime) -> tuple[str, str, str, str]:
    """
    Returns ('YYYY', 'MM', 'DD', 'HH') for building partitioned directories.
    """
    dtu = dt.astimezone(timezone.utc)
    return (
        dtu.strftime("%Y"),
        dtu.strftime("%m"),
        dtu.strftime("%d"),
        dtu.strftime("%H"),
    )
