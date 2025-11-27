from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from quantum.infrastructure.config.runtime.fsm_adapters import ConfigFSMAdapters
from quantum.infrastructure.config.runtime.fsm_model import (
    ConfigFSMState,
    ConfigLifecycleStatus,
)
from quantum.infrastructure.config.runtime.fsm_pipeline import ConfigFSMPipeline


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

    pipeline: ConfigFSMPipeline = ConfigFSMPipeline()
    adapters: ConfigFSMAdapters = ConfigFSMAdapters()

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
        Execute the entire deterministic configuration lifecycle.

        Returns:
            Final READY state containing:
                • env: Mapping[str, str]
                • settings: dict[str, Any]
                • metadata: dict[str, Any]
        """

        # 1. initial state
        state = ConfigFSMState.initial()

        # 2. resolve base directory + env path
        state = self.adapters.resolve_env_path(
            state,
            root=root,
            env_file=env_file,
        )

        # 3. load environment
        state = self.adapters.load_environment(
            state,
            root=root,
            env_file=env_file,
        )

        env = state.env
        if env is None:
            raise RuntimeError("FSM invariant violation: ENV_LOADED state without env.")

        # 4. construct raw settings
        state = self.adapters.build_models(
            state,
            env=env,
        )

        settings = state.settings
        if settings is None:
            raise RuntimeError(
                "FSM invariant violation: MODEL_BUILT state without settings."
            )

        # 5. validate settings (already done by Pydantic)
        state = self.adapters.validate_models(
            state,
            env=env,
            settings=settings,
        )

        # 6. freeze settings
        state = self.adapters.freeze_models(
            state,
            env=env,
            settings=settings,
        )

        # 7. final READY state
        state = self.adapters.finalize_ready(
            state,
            env=env,
            settings=settings,
        )

        if state.status is not ConfigLifecycleStatus.READY:
            raise RuntimeError(
                f"FSM lifecycle did not reach READY state, got: {state.status.value}"
            )

        return state
