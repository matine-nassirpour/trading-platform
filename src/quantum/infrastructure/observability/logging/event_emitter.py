import logging
from collections.abc import Mapping
from typing import Any

from quantum.shared.context.run_id import get_run_id
from quantum.shared.correlation.correlation_id import get_correlation_id

DEFAULT_LEVELS = {
    "order_reject_v1": logging.WARNING,
    "killswitch_trigger_v1": logging.ERROR,
}

_logger = logging.getLogger("quantum.trading")


def emit_event(
    event_model: Any,
    *,
    level: int | None = None,
    extra: Mapping[str, Any] | None = None,
) -> None:
    """
    Emit a structured trading *event* via logging infrastructure (JSON format).
    Accepts a Pydantic model or a dict. Injects run_id/correlation_id if missing.
    """
    if hasattr(event_model, "model_dump"):
        payload = event_model.model_dump(exclude_none=True)
    elif isinstance(event_model, dict):
        payload = {k: v for k, v in event_model.items() if v is not None}
    else:
        raise TypeError("event_model must be a pydantic model or dict")

    payload.setdefault("run_id", get_run_id())
    payload.setdefault("correlation_id", get_correlation_id())

    msg = payload.get("event_name") or "event"
    lvl = level or DEFAULT_LEVELS.get(msg, logging.INFO)

    # avoid overwriting "event" in LogRecord.extra
    safe_extra = {"event": payload}
    if extra:
        for k, v in extra.items():
            if k not in safe_extra:
                safe_extra[k] = v

    _logger.log(lvl, msg, extra=safe_extra)
