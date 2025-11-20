import threading

from dataclasses import dataclass, field


@dataclass(slots=True)
class InfoSamplerState:
    """
    Thread-safe state container for InfoSamplerStep.
    Explicit state externalization ensures:
        - Stateless step logic
        - Determinism
        - Clean Architecture compliance
        - Isolation of runtime-evolving state
    """

    sample_every: int
    counter: int = 0
    _lock: threading.Lock = field(
        default_factory=threading.Lock,
        init=False,
        repr=False,
        compare=False,
    )

    def increment_and_check(self) -> bool:
        """
        Increments the counter and returns True if the record should be emitted.
        """
        if self.sample_every <= 1:
            return True

        with self._lock:
            self.counter = (self.counter + 1) % self.sample_every
            return self.counter == 0
