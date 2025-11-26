"""
Quantum Core Configuration Contracts — Base Interfaces
──────────────────────────────────────────────────────
Defines abstract protocols and contracts governing interactions between
configuration models, providers, and runtime managers in the Quantum platform.

Responsibilities
----------------
- Define stable, type-safe interfaces for environment loading and state access.
- Ensure decoupling between configuration layers (models, providers, runtime).
- Provide strong typing guarantees for testing, mocking, and future refactors.
- Support interface-driven development and backward compatibility.

Design Principles
-----------------
- **Single Responsibility** : each protocol defines one cohesive role.
- **Interface Segregation** : clients depend only on the contracts they use.
- **Clean Architecture** : protocols reside in the innermost configuration layer.
- **Stability** : designed to remain invariant across runtime implementations.
- **Testability** : enables isolated, mockable configuration components.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Protocol, TypeVar, runtime_checkable

T = TypeVar("T", covariant=True)


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Environment Provider Contract                                              │
# ╰────────────────────────────────────────────────────────────────────────────╯
@runtime_checkable
class EnvProviderProtocol(Protocol):
    """
    Contract for any component responsible for loading environment variables.

    Implementations may load environment data from files (.env),
    process environment, secret managers, or composite sources.
    """

    def load_env(
        self,
        root: str | Path | None = None,
        env_file: str | Path | None = None,
        *,
        override: bool = False,
        apply: bool = False,
    ) -> dict[str, str]:
        """
        Load environment variables from one or more sources.

        Args:
            root: Optional root directory to resolve relative .env paths.
            env_file: Optional explicit .env file path.
            override: If True, existing environment variables are overwritten.
            apply: If True, the loaded variables are applied to os.environ.

        Returns:
            dict[str, str]: The merged environment mapping.
        """
        ...


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Configuration Loader Contract                                              │
# ╰────────────────────────────────────────────────────────────────────────────╯
@runtime_checkable
class ConfigLoaderProtocol(Protocol[T]):
    """
    Contract for any configuration loader capable of returning validated models.

    This protocol provides a stable abstraction for runtime managers, allowing
    dependency injection, testing, and custom loader substitution.
    """

    def load(self, **kwargs: Any) -> T:
        """
        Load a validated configuration model instance.

        Returns:
            T: The loaded and validated settings model.
        """
        ...


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Configuration State Contract                                               │
# ╰────────────────────────────────────────────────────────────────────────────╯
@runtime_checkable
class ConfigStateProtocol(Protocol):
    """
    Contract for thread-safe configuration state managers.

    Implementations are responsible for maintaining process-local configuration
    cache, environment snapshots, and atomic access to shared settings state.
    """

    def snapshot(self) -> dict[str, str | int | dict[str, str] | None]:
        """
        Return a deep copy of the current configuration state.

        The returned object must be immutable from the caller’s perspective.
        """
        ...

    def get_env_cache(self) -> dict[str, str]:
        """Return a shallow copy of the cached environment variables."""
        ...

    def update(
        self,
        *,
        base_dir: Path | None = None,
        loaded_pid: int | None = None,
        env_cache: dict[str, str] | None = None,
    ) -> None:
        """
        Atomically update the configuration state.

        Args:
            base_dir: Base directory where configuration was loaded.
            loaded_pid: Process ID associated with this state.
            env_cache: Cached mapping of merged environment variables.
        """
        ...

    def reset(self) -> None:
        """Reset configuration state to an empty, uninitialized state."""
        ...


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Configuration Snapshot Contract                                            │
# ╰────────────────────────────────────────────────────────────────────────────╯
@runtime_checkable
class ConfigSnapshotProtocol(Protocol):
    """
    Contract for components exposing read-only configuration summaries.

    This abstraction ensures all runtime components can provide a consistent
    and sanitized view of their configuration context (for metrics, logs, etc.).
    """

    def snapshot(self) -> Mapping[str, str]:
        """
        Return a minimal, non-sensitive configuration snapshot.

        Typically used for observability, health checks, or diagnostics.
        """
        ...
