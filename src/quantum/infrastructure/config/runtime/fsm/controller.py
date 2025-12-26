from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from quantum.infrastructure.config.runtime.fsm.model import (
    ConfigFSMState,
    ConfigLifecycleStatus,
)

# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Formal transition map (deterministic, acyclic)                             │
# ╰────────────────────────────────────────────────────────────────────────────╯
LEGAL_TRANSITIONS: Mapping[ConfigLifecycleStatus, set[ConfigLifecycleStatus]] = {
    ConfigLifecycleStatus.UNINITIALIZED: {
        ConfigLifecycleStatus.ENV_PATH_RESOLVED,
        ConfigLifecycleStatus.ERROR,
    },
    ConfigLifecycleStatus.ENV_PATH_RESOLVED: {
        ConfigLifecycleStatus.ENV_LOADED,
        ConfigLifecycleStatus.ERROR,
    },
    ConfigLifecycleStatus.ENV_LOADED: {
        ConfigLifecycleStatus.MODEL_BUILT,
        ConfigLifecycleStatus.ERROR,
    },
    ConfigLifecycleStatus.MODEL_BUILT: {
        ConfigLifecycleStatus.MODEL_VALIDATED,
        ConfigLifecycleStatus.ERROR,
    },
    ConfigLifecycleStatus.MODEL_VALIDATED: {
        ConfigLifecycleStatus.MODEL_FROZEN,
        ConfigLifecycleStatus.ERROR,
    },
    ConfigLifecycleStatus.MODEL_FROZEN: {
        ConfigLifecycleStatus.READY,
        ConfigLifecycleStatus.ERROR,
    },
    ConfigLifecycleStatus.READY: set(),  # terminal
    ConfigLifecycleStatus.ERROR: set(),  # terminal
}


@dataclass(slots=True)
class ConfigFSMController:
    """
    Pure functional state machine controller.

    • Enforces legal transitions
    • Produces new immutable FSM states
    • No side effects, no I/O
    • Compatible with formal verification (TLA+, Alloy)

    A controller instance is lightweight and stateless.
    """

    @staticmethod
    def _ensure_transition(
        current: ConfigFSMState,
        target: ConfigLifecycleStatus,
    ) -> None:
        allowed = LEGAL_TRANSITIONS[current.status]
        if target not in allowed:
            raise ValueError(
                f"Illegal FSM transition: {current.status.value} → {target.value}. "
                f"Allowed: {[s.value for s in allowed]}"
            )

    # --------------------------------------------------------------------------
    # Transition methods (pure)
    # --------------------------------------------------------------------------
    def step_env_path_resolved(
        self,
        current: ConfigFSMState,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> ConfigFSMState:
        """Transition UNINITIALIZED → ENV_PATH_RESOLVED"""
        target = ConfigLifecycleStatus.ENV_PATH_RESOLVED
        self._ensure_transition(current, target)

        return ConfigFSMState(
            status=target,
            env=None,
            settings=None,
            metadata=metadata or {},
        )

    def step_env_loaded(
        self,
        current: ConfigFSMState,
        *,
        env: dict[str, str],
        metadata: dict[str, Any] | None = None,
    ) -> ConfigFSMState:
        """Transition ENV_PATH_RESOLVED → ENV_LOADED"""
        target = ConfigLifecycleStatus.ENV_LOADED
        self._ensure_transition(current, target)

        return ConfigFSMState(
            status=target,
            env=dict(env),  # shallow copy for safety
            settings=None,
            metadata=metadata or {},
        )

    def step_model_built(
        self,
        current: ConfigFSMState,
        *,
        env: dict[str, str],
        settings: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> ConfigFSMState:
        """Transition ENV_LOADED → MODEL_BUILT"""
        target = ConfigLifecycleStatus.MODEL_BUILT
        self._ensure_transition(current, target)

        return ConfigFSMState(
            status=target,
            env=dict(env),
            settings=dict(settings),
            metadata=metadata or {},
        )

    def step_model_validated(
        self,
        current: ConfigFSMState,
        *,
        env: dict[str, str],
        settings: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> ConfigFSMState:
        """Transition MODEL_BUILT → MODEL_VALIDATED"""
        target = ConfigLifecycleStatus.MODEL_VALIDATED
        self._ensure_transition(current, target)

        return ConfigFSMState(
            status=target,
            env=dict(env),
            settings=dict(settings),
            metadata=metadata or {},
        )

    def step_model_frozen(
        self,
        current: ConfigFSMState,
        *,
        env: dict[str, str],
        settings: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> ConfigFSMState:
        """Transition MODEL_VALIDATED → MODEL_FROZEN"""
        target = ConfigLifecycleStatus.MODEL_FROZEN
        self._ensure_transition(current, target)

        return ConfigFSMState(
            status=target,
            env=dict(env),
            settings=dict(settings),
            metadata=metadata or {},
        )

    def step_ready(
        self,
        current: ConfigFSMState,
        *,
        env: dict[str, str],
        settings: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> ConfigFSMState:
        """Transition MODEL_FROZEN → READY"""
        target = ConfigLifecycleStatus.READY
        self._ensure_transition(current, target)

        return ConfigFSMState(
            status=target,
            env=dict(env),
            settings=dict(settings),
            metadata=metadata or {},
        )

    @staticmethod
    def step_error(
        current: ConfigFSMState,
        message: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> ConfigFSMState:
        """Transition ANY → ERROR (always legal)"""
        # No need to call _ensure_transition: ERROR is always allowed
        return ConfigFSMState(
            status=ConfigLifecycleStatus.ERROR,
            env=current.env,
            settings=current.settings,
            error=message,
            metadata=metadata or {},
        )
