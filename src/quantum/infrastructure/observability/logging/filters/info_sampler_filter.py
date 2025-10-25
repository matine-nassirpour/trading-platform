import logging
import threading


class InfoSamplerFilter(logging.Filter):
    """
    Samples INFO-level log records at a fixed interval.
    """

    def __init__(self, sample_every: int = 10):
        super().__init__()
        self._sample_every = max(1, int(sample_every))  # <=1 → no sampling
        self._counter = 0
        self._lock = threading.Lock()

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Allows one INFO-level record every N occurrences; passes all other levels unmodified.
        Thread-safe.
        """
        if record.levelno != logging.INFO or self._sample_every <= 1:
            return True

        with self._lock:
            self._counter = (self._counter + 1) % self._sample_every
            return self._counter == 0
