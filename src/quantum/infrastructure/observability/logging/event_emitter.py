import logging
from collections.abc import Mapping
from typing import Any, Final

from quantum.shared.context.run_id import get_run_id
from quantum.shared.correlation.correlation_id import get_correlation_id

# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Constants                                                                  │
# ╰────────────────────────────────────────────────────────────────────────────╯
DEFAULT_EVENT_LEVELS: Final[dict[str, int]] = {
    "order_reject_v1": logging.WARNING,
    "killswitch_trigger_v1": logging.ERROR,
}

_LOGGER: Final[logging.Logger] = logging.getLogger("quantum.trading")


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Public API                                                                 │
# ╰────────────────────────────────────────────────────────────────────────────╯
def emit_event(
    event_model: Any,
    *,
    level: int | None = None,
    extra: Mapping[str, Any] | None = None,
) -> None:
    """
    Emit a structured trading event to the observability logging system.

    Accepts either a Pydantic model (with `.model_dump`) or a raw dict.
    Automatically injects contextual fields (`run_id`, `correlation_id`)
    if missing, ensuring full traceability across the event pipeline.

    Args:
        event_model: A Pydantic model or dict representing the event payload.
        level: Optional explicit log level (int). If not provided, a default
            severity is selected based on the event name or defaults to INFO.
        extra: Optional extra fields to include in the log record's context.

    Behavior
    --------
    - Converts model to a JSON-safe dict.
    - Ensures event correlation consistency.
    - Delegates to the `"quantum.trading"` logger.
    - Never raises; logging failures are handled by downstream handlers.

    Raises:
        TypeError: if `event_model` is not a dict or Pydantic-compatible object.
    """
    # Convert to dict (support Pydantic models and plain dicts)
    if hasattr(event_model, "model_dump"):
        payload: dict[str, Any] = event_model.model_dump(exclude_none=True)
    elif isinstance(event_model, dict):
        payload = {k: v for k, v in event_model.items() if v is not None}
    else:
        raise TypeError("event_model must be a Pydantic model or a dict")

    # Inject contextual IDs if absent
    payload.setdefault("run_id", get_run_id())
    payload.setdefault("correlation_id", get_correlation_id())

    event_name = payload.get("event_name") or "event"
    log_level = level or DEFAULT_EVENT_LEVELS.get(event_name, logging.INFO)

    # Compose safe 'extra' field
    safe_extra: dict[str, Any] = {"event": payload}
    if extra:
        for k, v in extra.items():
            if k not in safe_extra:
                safe_extra[k] = v

    _LOGGER.log(log_level, event_name, extra=safe_extra)
