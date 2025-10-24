import logging
import threading


class InfoSamplerFilter(logging.Filter):
    def __init__(self, sample_every: int = 10):
        super().__init__()
        self._n = max(1, int(sample_every))  # <=1 → no sampling
        self._i = 0
        self._lock = threading.Lock()

    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelno != logging.INFO or self._n <= 1:
            return True
        with self._lock:
            self._i = (self._i + 1) % self._n
            return self._i == 0
