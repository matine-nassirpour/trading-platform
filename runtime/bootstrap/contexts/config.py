from quantum.infrastructure.config.models.core import CoreSettings


class RuntimeConfigContext:
    """
    Immutable runtime configuration context.

    Responsibility:
    - Expose validated runtime configuration
    - Act as a read-only boundary for deployment/runtime wiring
    """

    def __init__(self, *, core_settings: CoreSettings) -> None:
        self._core = core_settings

    @property
    def core(self) -> CoreSettings:
        return self._core
