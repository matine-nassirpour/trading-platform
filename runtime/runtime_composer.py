"""
Quantum Runtime Composer
────────────────────────
Central composition root responsible for assembling the Quantum
runtime dependency graph in a clean, explicit, and certifiable way.

Responsibilities
----------------
- Wire up application ports to their infrastructure adapters.
- Provide a unified entry point for Streamlit, CLI, or other interfaces.
- Guarantee strict compliance with Clean Architecture (DIP).
- Serve as a testable and auditable composition layer (no business logic).

Design Principles
-----------------
- Single Responsibility: assembles dependencies, nothing more.
- Inversion of Control: injects implementations into abstractions.
- Framework Independence: runtime wiring is explicit and isolated.
- Transparency: dependencies are declared, not auto-magically resolved.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from quantum.application.ports.outbound.config_port import ConfigPort
from quantum.application.ports.outbound.logging_port import LoggingPort
from quantum.application.ports.outbound.observability_port import ObservabilityPort
from quantum.infrastructure.config.adapters.config_provider_adapter import (
    ConfigProviderAdapter,
)
from quantum.infrastructure.observability.adapters.logging_provider_adapter import (
    LoggingProviderAdapter,
)
from quantum.infrastructure.observability.adapters.observability_provider_adapter import (
    ObservabilityProviderAdapter,
)


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Data structure representing the composed runtime context                   │
# ╰────────────────────────────────────────────────────────────────────────────╯
@dataclass(frozen=True, slots=True)
class QuantumRuntimeContext:
    """
    Aggregates all active providers implementing outbound ports.

    This structure defines the dependency graph available to
    any interface layer (UI, CLI, API, etc.).
    """

    config_provider: ConfigPort
    logging_provider: LoggingPort
    observability_provider: ObservabilityPort

    def describe(self) -> dict[str, str]:
        return {
            "config_provider": type(self.config_provider).__name__,
            "logging_provider": type(self.logging_provider).__name__,
            "observability_provider": type(self.observability_provider).__name__,
        }


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Composer (factory for the runtime context)                                 │
# ╰────────────────────────────────────────────────────────────────────────────╯
class RuntimeComposer:
    """
    Responsible for assembling the full runtime dependency graph.
    """

    _instance: QuantumRuntimeContext | None = None

    @classmethod
    def compose(cls) -> QuantumRuntimeContext:
        """
        Build and cache the Quantum runtime context.
        """
        if cls._instance is not None:
            return cls._instance

        logger = logging.getLogger(__name__)
        logger.info("Assembling Quantum runtime context...")

        config_provider = ConfigProviderAdapter()
        logging_provider = LoggingProviderAdapter()
        observability_provider = ObservabilityProviderAdapter()

        cls._instance = QuantumRuntimeContext(
            config_provider=config_provider,
            logging_provider=logging_provider,
            observability_provider=observability_provider,
        )

        logging.getLogger(__name__).info(
            "Quantum runtime context assembled successfully: %s",
            cls._instance.describe(),
        )

        return cls._instance


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Global accessor                                                            │
# ╰────────────────────────────────────────────────────────────────────────────╯
def get_runtime() -> QuantumRuntimeContext:
    """
    Retrieve the active Quantum runtime context (singleton instance).
    """
    return RuntimeComposer.compose()
