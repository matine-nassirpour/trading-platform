from __future__ import annotations

import logging

from typing import Final

from quantum.infrastructure.config.validators.base import (
    ValidationResult,
    ValidationRule,
)
from quantum.infrastructure.config.validators.policy import STRICT_VALIDATION

LOGGER: Final = logging.getLogger(__name__)


class EnvironmentValidator(ValidationRule):
    def __init__(self) -> None:
        super().__init__(
            "platform.runtime.environment",
            "Validate and normalize runtime environment.",
        )
        self._allowed = {"dev", "test", "staging", "prod"}

    def __call__(self, value: str, *, context=None) -> ValidationResult:
        if not value or not value.strip():
            return self.success("dev")

        v = value.strip().lower()
        if v not in self._allowed:
            msg = f"Invalid environment '{v}', allowed: {sorted(self._allowed)}"
            return self.failure(msg, value=v)

        return self.success(v)


class LogLevelValidator(ValidationRule):
    def __init__(self) -> None:
        super().__init__(
            "platform.logging.log_level", "Validate and normalize logging level."
        )
        self._allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

    def __call__(self, value: str, *, context=None) -> ValidationResult:
        if not value:
            return self.success("INFO")

        v = value.strip().upper()
        if v not in self._allowed:
            msg = f"Invalid log level '{v}', allowed: {sorted(self._allowed)}"
            return self.failure(msg, value=v)

        return self.success(v)


class TimezoneValidator(ValidationRule):
    def __init__(self) -> None:
        super().__init__(
            rule_id="platform.logging.timezone",
            description="Validate timezone specifier ('utc' or 'local').",
        )

    def __call__(self, value: str, *, context=None) -> ValidationResult:
        if value is None:
            return self.success("utc")

        v = value.strip().lower()
        if v not in ("utc", "local"):
            return self.failure("Timezone must be 'utc' or 'local'", value=v)

        return self.success(v)


class OtlpProtocolValidator(ValidationRule):
    def __init__(self) -> None:
        super().__init__("platform.tracing.otlp_protocol", "Validate OTLP protocol.")
        self._allowed = {"http", "grpc"}

    def __call__(self, value: str, *, context=None) -> ValidationResult:
        if not value:
            return self.success("http")

        v = value.strip().lower()
        if v not in self._allowed:
            msg = f"Invalid OTLP protocol '{v}', allowed: {sorted(self._allowed)}"

            if STRICT_VALIDATION:
                return self.failure(msg, value=v)

            LOGGER.warning(
                "%s; falling back to 'http' due to non-strict validation mode.",
                msg,
            )
            return self.success("http")

        return self.success(v)


class CompressionValidator(ValidationRule):
    def __init__(self) -> None:
        super().__init__(
            "platform.tracing.compression", "Validate OTLP compression mode."
        )
        self._allowed = {"gzip", "none"}

    def __call__(self, value: str, *, context=None) -> ValidationResult:
        if not value:
            return self.success("none")

        v = value.strip().lower()
        if v not in self._allowed:
            msg = f"Invalid compression '{v}', allowed: {sorted(self._allowed)}"

            if STRICT_VALIDATION:
                return self.failure(msg, value=v)

            LOGGER.warning(
                "%s; falling back to 'none' due to non-strict validation mode.",
                msg,
            )
            return self.success("none")

        return self.success(v)
