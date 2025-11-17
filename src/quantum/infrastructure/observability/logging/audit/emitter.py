import logging

from collections.abc import Mapping
from typing import Any, Final

_LOGGER: Final[logging.Logger] = logging.getLogger("quantum.trading.audit")


def emit_event(
    event_model: Any,
    *,
    level: int | None = None,
    extra: Mapping[str, Any] | None = None,
) -> None:
    """
    Emit a structured trading event to the observability logging system.
    Accepts either a Pydantic model (with `.model_dump`) or a raw dict.
    Converts model to a JSON-safe dict.
    """
    # Convert to dict (support Pydantic models and plain dicts)
    if hasattr(event_model, "model_dump"):
        payload: dict[str, Any] = event_model.model_dump(exclude_none=True)
    elif isinstance(event_model, dict):
        payload = {k: v for k, v in event_model.items() if v is not None}
    else:
        raise TypeError("event_model must be a Pydantic model or a dict")

    event_name = payload.get("event_name") or "event"
    log_level = level or logging.INFO

    # Compose `extra`
    safe_extra: dict[str, Any] = {"event": payload}
    if extra:
        for k, v in extra.items():
            if k not in safe_extra:
                safe_extra[k] = v

    _LOGGER.log(log_level, event_name, extra=safe_extra)
