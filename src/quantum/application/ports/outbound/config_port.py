from typing import Protocol

from quantum.application.dto.config_bundle import QuantumConfigBundle


class ConfigPort(Protocol):
    """Structural interface for accessing validated configuration bundles."""

    def get_bundle(self) -> QuantumConfigBundle:
        """Return the current, validated configuration bundle."""
        ...

    def refresh_bundle(self) -> QuantumConfigBundle:
        """Invalidate caches and reload configuration from authoritative sources."""
        ...
