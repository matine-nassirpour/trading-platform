from typing import Protocol, runtime_checkable

from quantum.infrastructure.observability.bootstrap.lifecycle.configs.logging_config import (
    LoggingConfig,
)


@runtime_checkable
class LoggingInitializer(Protocol):
    """
    Abstraction defining the contract for initializing and shutting down
    the logging subsystem.

    Implementations may:
      • Configure JSON logging
      • Install handlers
      • Configure audit sinks
      • Install filters / formatting
      • Ensure durability (fsync)
      • Support rotation, sharding, partitioning

    This interface is testable and framework-agnostic.
    """

    def initialize(self, config: LoggingConfig) -> bool:
        """
        Initialize logging given an immutable logging config.

        Returns:
            True if initialization succeeded; False otherwise.
        """
        ...

    def shutdown(self) -> None:
        """Gracefully close logging handlers and persistent sinks."""
        ...
