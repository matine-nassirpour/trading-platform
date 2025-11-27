from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any


class ConfigLifecycleStatus(str, Enum):
    """
    Formal lifecycle states for the configuration finite state machine.

    The lifecycle is strictly monotonic:
        UNINITIALIZED → ENV_PATH_RESOLVED → ENV_LOADED →
        MODEL_BUILT → MODEL_VALIDATED → MODEL_FROZEN → READY

    An ERROR state is allowed and terminal.
    """

    UNINITIALIZED = "uninitialized"
    ENV_PATH_RESOLVED = "env_path_resolved"
    ENV_LOADED = "env_loaded"
    MODEL_BUILT = "model_built"
    MODEL_VALIDATED = "model_validated"
    MODEL_FROZEN = "model_frozen"
    READY = "ready"
    ERROR = "error"


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Invariant functions (one per state)                                        │
# ╰────────────────────────────────────────────────────────────────────────────╯
def _inv_error(state: ConfigFSMState) -> None:
    if not state.error:
        raise ValueError("ERROR state requires non-empty 'error' message.")


def _inv_uninitialized(state: ConfigFSMState) -> None:
    if state.env is not None or state.settings is not None or state.error is not None:
        raise ValueError("UNINITIALIZED must not carry env/settings/error.")


def _inv_env_path_resolved(state: ConfigFSMState) -> None:
    # env must be None; settings and error must be None
    if state.env is not None:
        raise ValueError("ENV_PATH_RESOLVED must not carry env.")
    if state.settings is not None or state.error is not None:
        raise ValueError("ENV_PATH_RESOLVED must not carry settings/error.")


def _inv_env_loaded(state: ConfigFSMState) -> None:
    if state.env is None:
        raise ValueError("ENV_LOADED requires 'env' to be populated.")
    if state.settings is not None:
        raise ValueError("ENV_LOADED must not carry 'settings'.")
    if state.error is not None:
        raise ValueError("ENV_LOADED must not carry 'error'.")


def _inv_model_built(state: ConfigFSMState) -> None:
    if state.env is None or state.settings is None:
        raise ValueError("MODEL_BUILT requires both 'env' and 'settings'.")
    if state.error is not None:
        raise ValueError("MODEL_BUILT must not carry 'error'.")


def _inv_model_validated(state: ConfigFSMState) -> None:
    if state.env is None or state.settings is None:
        raise ValueError("MODEL_VALIDATED requires both 'env' and 'settings'.")
    if state.error is not None:
        raise ValueError("MODEL_VALIDATED must not carry 'error'.")


def _inv_model_frozen(state: ConfigFSMState) -> None:
    if state.env is None or state.settings is None:
        raise ValueError("MODEL_FROZEN requires both 'env' and 'settings'.")
    if state.error is not None:
        raise ValueError("MODEL_FROZEN must not carry 'error'.")


def _inv_ready(state: ConfigFSMState) -> None:
    if state.env is None or state.settings is None:
        raise ValueError("READY requires both 'env' and 'settings'.")
    if state.error is not None:
        raise ValueError("READY must not carry 'error'.")


_INVARIANTS = {
    ConfigLifecycleStatus.ERROR: _inv_error,
    ConfigLifecycleStatus.UNINITIALIZED: _inv_uninitialized,
    ConfigLifecycleStatus.ENV_PATH_RESOLVED: _inv_env_path_resolved,
    ConfigLifecycleStatus.ENV_LOADED: _inv_env_loaded,
    ConfigLifecycleStatus.MODEL_BUILT: _inv_model_built,
    ConfigLifecycleStatus.MODEL_VALIDATED: _inv_model_validated,
    ConfigLifecycleStatus.MODEL_FROZEN: _inv_model_frozen,
    ConfigLifecycleStatus.READY: _inv_ready,
}


@dataclass(frozen=True, slots=True)
class ConfigFSMState:
    """
    Immutable, safety-grade snapshot of the configuration lifecycle state.

    Invariants:
        • status encodes the lifecycle phase
        • env is only populated from ENV_LOADED onward
        • settings is only populated from MODEL_BUILT onward
        • error is only populated in ERROR state
        • metadata is always immutable (mapping proxy)
    """

    status: ConfigLifecycleStatus
    env: Mapping[str, str] | None = None
    settings: Mapping[str, Any] | None = None
    error: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        """
        Enforce state invariants at construction time.

        This method MUST NOT perform any I/O or side effects.
        It is purely structural validation compatible with safety-critical contexts.
        """
        # Enforce metadata immutability
        object.__setattr__(
            self, "metadata", MappingProxyType(dict(self.metadata or {}))
        )

        # Dispatch invariant checks
        invariant_fn = _INVARIANTS.get(self.status)
        if invariant_fn is None:
            raise ValueError(f"No invariants defined for state {self.status}")
        invariant_fn(self)

    # --------------------------------------------------------------------------
    # Factory helpers for canonical states
    # --------------------------------------------------------------------------
    @staticmethod
    def initial() -> ConfigFSMState:
        """Return the canonical initial state."""
        return ConfigFSMState(status=ConfigLifecycleStatus.UNINITIALIZED)

    def to_error(self, message: str) -> ConfigFSMState:
        """
        Transition helper to an ERROR state, preserving metadata.

        NOTE: This does not implement a full FSM transition yet;
        it is a pure convenience constructor.
        """
        return ConfigFSMState(
            status=ConfigLifecycleStatus.ERROR,
            env=self.env,
            settings=self.settings,
            error=message,
            metadata=self.metadata,
        )
