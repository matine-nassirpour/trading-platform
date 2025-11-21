from __future__ import annotations

import logging

from typing import Final

from quantum.infrastructure.observability.bootstrap.lifecycle.configs.logging_config import (
    LoggingConfig,
)
from quantum.infrastructure.observability.foundation.config.logging_runtime_bundle import (
    LoggingRuntimeBundle,
)
from quantum.infrastructure.observability.logging.api.logging_service import (
    close_and_remove_all_handlers,
    init_logging,
)

LOGGER: Final = logging.getLogger(__name__)


class LoggingInitializerImpl:
    """
    Clean-Architecture adapter converting a high-level LoggingConfig
    (application-facing VO) into a LoggingRuntimeBundle (logging-internal VO).
    """

    def __init__(self) -> None:
        self._initialized = False

    def initialize(self, config: LoggingConfig) -> bool:
        if self._initialized:
            return True

        try:
            bundle = LoggingRuntimeBundle(
                environment=config.environment,
                service_namespace=config.service_namespace,
                service_name=config.service_name,
                service_version=config.service_version,
                instance_id=config.instance_id,
                log_dir=config.log_dir,
                audit_dir=config.audit_dir,
                audit_allowlist=config.audit_allowlist,
                log_level=config.log_level,
                sample_info_every=config.sample_info_every,
                ratelimit_rps=config.ratelimit_rps,
                log_fsync=config.log_fsync,
                log_max_bytes=config.log_max_bytes,
                log_warn_bytes=config.log_warn_bytes,
                enable_partition_handler=config.log_dir is not None,
            )

            init_logging(bundle)
            self._initialized = True
            return True

        except Exception as exc:
            LOGGER.error(
                "Logging initialization failed: %s",
                exc,
                exc_info=True,
            )
            return False

    def shutdown(self) -> None:
        try:
            # Close handlers of the application logger only
            app_logger = logging.getLogger("quantum.app")
            close_and_remove_all_handlers(app_logger)

        except Exception as exc:
            LOGGER.debug(
                "Failed during logging shutdown: %s",
                exc,
                exc_info=True,
            )
        finally:
            self._initialized = False
