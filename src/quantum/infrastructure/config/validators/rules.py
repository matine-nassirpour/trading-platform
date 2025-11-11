"""
Quantum Core Configuration Validators — Common Rules
─────────────────────────────────────────────────────
Defines reusable validation rules shared across all
configuration models (log level, timezone, protocol, etc.).
"""

from __future__ import annotations

import logging

from quantum.infrastructure.config.validators.base import (
    ValidationContext,
    ValidationResult,
    ValidationRule,
)


class EnvironmentValidator(ValidationRule):
    def __init__(self) -> None:
        super().__init__(
            rule_id="platform.runtime.environment",
            description="Validate and normalize runtime environment identifiers.",
        )
        self._allowed = {"dev", "test", "staging", "prod"}

    def __call__(
        self, value: str, *, context: ValidationContext | None = None
    ) -> ValidationResult:
        if not value or value.strip() == "":
            return self.success("dev")
        v = value.strip().lower()
        if v not in self._allowed:
            msg = f"Invalid environment '{v}', expected one of {sorted(self._allowed)}"
            return self.failure(msg, value=v)
        return self.success(v)


class LogLevelValidator(ValidationRule):
    def __init__(self) -> None:
        super().__init__(
            rule_id="platform.logging.log_level",
            description="Validate and normalize log level names.",
        )
        self._allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

    def __call__(
        self, value: str, *, context: ValidationContext | None = None
    ) -> ValidationResult:
        if not value:
            return self.success("INFO")
        v = value.strip().upper()
        if v not in self._allowed:
            msg = f"Invalid log level '{v}', expected one of {sorted(self._allowed)}"
            return self.failure(msg, value=v)
        return self.success(v)


class TimezoneValidator(ValidationRule):
    def __init__(self) -> None:
        super().__init__(
            rule_id="platform.logging.timezone",
            description="Validate timezone specifier ('utc' or 'local').",
        )

    def __call__(
        self, value: str, *, context: ValidationContext | None = None
    ) -> ValidationResult:
        if value is None:
            return self.success("utc")
        v = value.strip().lower()
        if v not in ("utc", "local"):
            return self.failure("Timezone must be 'utc' or 'local'", value=v)
        return self.success(v)


class OtlpProtocolValidator(ValidationRule):
    def __init__(self) -> None:
        super().__init__(
            rule_id="platform.tracing.otlp_protocol",
            description="Validate OpenTelemetry OTLP protocol ('http' or 'grpc').",
        )
        self._allowed = {"http", "grpc"}

    def __call__(
        self, value: str, *, context: ValidationContext | None = None
    ) -> ValidationResult:
        if not value:
            return self.success("http")
        v = value.strip().lower()
        if v not in self._allowed:
            logging.getLogger(__name__).warning(
                f"Unsupported OTLP protocol '{v}', defaulting to 'http'"
            )
            v = "http"
        return self.success(v)


class CompressionValidator(ValidationRule):
    def __init__(self) -> None:
        super().__init__(
            rule_id="platform.tracing.compression",
            description="Validate OTLP compression mode ('gzip' or 'none').",
        )
        self._allowed = {"gzip", "none"}

    def __call__(
        self, value: str, *, context: ValidationContext | None = None
    ) -> ValidationResult:
        if not value:
            return self.success("none")
        v = value.strip().lower()
        if v not in self._allowed:
            msg = f"Invalid compression '{v}', must be one of {sorted(self._allowed)}"
            return self.failure(msg, value=v)
        return self.success(v)
