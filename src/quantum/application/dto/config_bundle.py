from dataclasses import dataclass

from quantum.contracts.settings_contracts import (
    CoreSettingsContract,
    LoggingSettingsContract,
    MT5SettingsContract,
    TracingSettingsContract,
)


@dataclass(frozen=True, slots=True)
class QuantumConfigBundle:
    """Aggregated configuration model for the Quantum runtime.

    Each sub-model must be a validated, read-only dataclass instance
    originating from the infrastructure configuration subsystem.
    """

    core: CoreSettingsContract
    logging: LoggingSettingsContract
    tracing: TracingSettingsContract
    mt5: MT5SettingsContract
