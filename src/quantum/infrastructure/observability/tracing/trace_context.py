from contextlib import suppress

from opentelemetry.trace import get_current_span


def extract_trace_context() -> tuple[str | None, str | None, bool | None]:
    """Extracts (trace_id, span_id, sampled) from the current OpenTelemetry span"""
    try:
        span = get_current_span()
        sc = span.get_span_context()
    except Exception:
        return None, None, None

    try:
        is_valid = bool(getattr(sc, "is_valid", False))
    except Exception:
        is_valid = False

    if not is_valid:
        return None, None, None

    trace_id = span_id = sampled = None

    with suppress(Exception):
        trace_id = f"{int(getattr(sc, 'trace_id', 0)):032x}"
    with suppress(Exception):
        span_id = f"{int(getattr(sc, 'span_id', 0)):016x}"

    with suppress(Exception):
        flags = getattr(sc, "trace_flags", None)
        if flags is not None:
            sampled = getattr(flags, "sampled", None)
            if not isinstance(sampled, bool):
                sampled = bool(int(flags) & 0x01)

    return trace_id, span_id, sampled
