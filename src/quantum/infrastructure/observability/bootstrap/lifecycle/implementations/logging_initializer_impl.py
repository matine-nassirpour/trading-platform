from __future__ import annotations

import logging

from quantum.infrastructure.config.models.core import CoreSettings
from quantum.infrastructure.config.models.logging import LoggingSettings
from quantum.infrastructure.observability.bootstrap.lifecycle.configs.logging_config import (
    LoggingConfig,
)
from quantum.infrastructure.observability.bootstrap.lifecycle.protocols.logging_initializer import (
    LoggingInitializer,
)
from quantum.infrastructure.observability.logging.service import (
    close_and_remove_all_handlers,
    init_logging,
)


class LoggingInitializerImpl(LoggingInitializer):
    """
    Concrete LoggingInitializer implementation that adapts the LoggingConfig
    Value Object into the existing Quantum logging subsystem.

    This is the adapter layer between Clean Architecture and the logging stack.
    """

    def __init__(self) -> None:
        self._initialized = False

    def initialize(self, config: LoggingConfig) -> bool:
        if self._initialized:
            return True

        try:
            core = CoreSettings(
                quantum_env=config.environment,
                quantum_ns=config.service_namespace,
                quantum_app_name=config.service_name,
                quantum_app_version=config.service_version,
                quantum_instance_id=config.instance_id,
            )

            logging_cfg = LoggingSettings(
                quantum_log_level=str(config.level),
                quantum_log_dir=(
                    str(config.log_directory) if config.log_directory else None
                ),
                quantum_audit_dir=(
                    str(config.audit_directory) if config.audit_directory else None
                ),
                quantum_log_rps=config.rate_limit_per_sec,
                quantum_log_sample_info=config.sample_info_every,
                quantum_log_deep_probe=config.deep_probe,
            )

            init_logging(core, logging_cfg)
            self._initialized = True
            return True

        except Exception:
            return False

    def shutdown(self) -> None:
        try:
            close_and_remove_all_handlers(logging.getLogger())
        except Exception as exc:
            logging.getLogger(__name__).debug(
                "Failed to close existing logging handlers during reinitialization: %s",
                exc,
            )
        finally:
            self._initialized = False
