import logging
from collections.abc import Iterable
from typing import Final

_NOISY_LOGGER_PREFIXES: Final[set[str]] = {
    "urllib3.connectionpool",
    "requests.packages.urllib3.connectionpool",
    "opentelemetry.sdk._logs",
    "opentelemetry.sdk.trace",
    "opentelemetry.sdk.trace.export",
    "opentelemetry.sdk._shared_internal",
}


class IgnoreLibrariesFilter(logging.Filter):
    """
    Filters out log records originating from known noisy third-party libraries.
    """

    def __init__(self, noisy_prefixes: Iterable[str] | None = None) -> None:
        super().__init__()
        self._noisy_prefixes = (
            set(noisy_prefixes) if noisy_prefixes else _NOISY_LOGGER_PREFIXES
        )

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Return True if the record does not originate from a noisy library.
        """
        name = getattr(record, "name", "")
        for prefix in self._noisy_prefixes:
            if name.startswith(prefix):
                return False
        return True
