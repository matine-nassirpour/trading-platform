import logging

from prometheus_client import REGISTRY

_logger = logging.getLogger(__name__)


def get_gauge_value(name: str) -> float | None:
    """Return the value of a gauge metric without labels."""
    try:
        for metric in REGISTRY.collect():
            for s in getattr(metric, "samples", ()):
                if s.name == name and not s.labels:
                    return float(s.value)
        return None
    except Exception as exc:
        _logger.debug("gauge_value(%s) failed: %s", name, exc)
        return None


def get_counter_value(name: str) -> float | None:
    """Alias to get_gauge_value (for counter metrics)."""
    return get_gauge_value(name)
