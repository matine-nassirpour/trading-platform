from __future__ import annotations

from typing import Final

from quantum.infrastructure.config.models.core import CoreSettings
from quantum.infrastructure.observability.foundation.config.identity_runtime_bundle import (
    IdentityRuntimeBundle,
)


class RuntimeIdentityContext:
    """
    Immutable runtime identity context.

    Responsibility:
    - Provide a canonical, validated runtime identity
    - Serve as the single source of truth for service identity

    No lifecycle.
    No side effects.
    """

    def __init__(self, *, core_settings: CoreSettings) -> None:
        self._identity: Final = IdentityRuntimeBundle(
            environment=core_settings.quantum_env,
            service_namespace=core_settings.quantum_ns,
            service_name=core_settings.quantum_app_name,
            service_version=core_settings.quantum_app_version,
            instance_id=core_settings.quantum_instance_id or "unknown",
        )

    @property
    def identity(self) -> IdentityRuntimeBundle:
        return self._identity
