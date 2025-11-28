from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from quantum.infrastructure.config.runtime.fsm.adapters import ConfigFSMAdapters
from quantum.infrastructure.config.runtime.fsm.model import (
    ConfigFSMState,
    ConfigLifecycleStatus,
)
from quantum.infrastructure.config.runtime.fsm.pipeline import ConfigFSMPipeline


@dataclass(slots=True)
class ConfigFSMOrchestrator:
    """
    High-level orchestrator driving the entire configuration lifecycle.

    This is the imperative shell controlling:
        • environment resolution
        • environment loading
        • model construction
        • model validation
        • model freezing
        • final readiness

    All impurity and I/O is strictly delegated to adapters.
    All state evolution is done through the pure FSM pipeline.
    """

    pipeline: ConfigFSMPipeline = field(default_factory=ConfigFSMPipeline)
    adapters: ConfigFSMAdapters = field(default_factory=ConfigFSMAdapters)

    # --------------------------------------------------------------------------
    # High-level run sequence
    # --------------------------------------------------------------------------
    def run_full_lifecycle(
        self,
        *,
        root: str | Path | None = None,
        env_file: str | Path | None = None,
    ) -> ConfigFSMState:
        """
        Execute the entire configuration lifecycle and return a READY state.

        Returns:
            • env: Mapping[str, str]
            • settings: dict[str, Any]
            • metadata: dict[str, Any]
        """

        # 1. Initial FSM state
        state = ConfigFSMState.initial()

        # 2. PURE RESOLVE — produces new FSM state + resolution VO
        state, resolution = self.adapters.resolve_env_path(
            state,
            root=root,
            env_file=env_file,
        )

        # 3. LOAD ENVIRONMENT — impure, called ONLY ONCE
        state = self.adapters.load_environment(
            state,
            resolution=resolution,
            root_param=root,
            env_file_param=env_file,
        )

        env = state.env
        if env is None:
            raise RuntimeError(
                "Configuration FSM invariant violation: missing env in ENV_LOADED state."
            )

        # 4. BUILD MODELS (impure Pydantic construction)
        state = self.adapters.build_models(
            state,
            env=env,
        )

        settings = state.settings
        if settings is None:
            raise RuntimeError(
                "Configuration FSM invariant violation: missing settings in MODEL_BUILT state."
            )

        # 5. VALIDATE MODELS (pure, external validation already applied by Pydantic)
        state = self.adapters.validate_models(
            state,
            env=env,
            settings=settings,
        )

        # 6. FREEZE MODELS (pure)
        state = self.adapters.freeze_models(
            state,
            env=env,
            settings=settings,
        )

        # 7. READY (pure)
        state = self.adapters.finalize_ready(
            state,
            env=env,
            settings=settings,
        )

        if state.status is not ConfigLifecycleStatus.READY:
            raise RuntimeError(
                f"FSM lifecycle did not reach READY state — got: {state.status.value}"
            )

        return state
