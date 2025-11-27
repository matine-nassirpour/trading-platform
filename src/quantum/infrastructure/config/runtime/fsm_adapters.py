from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quantum.infrastructure.config.models.core import CoreSettings
from quantum.infrastructure.config.models.logging import LoggingSettings
from quantum.infrastructure.config.models.mt5 import MT5Settings
from quantum.infrastructure.config.models.tracing import TracingSettings
from quantum.infrastructure.config.providers.env_loader import load_env
from quantum.infrastructure.config.runtime.fsm_model import ConfigFSMState
from quantum.infrastructure.config.runtime.fsm_pipeline import ConfigFSMPipeline


@dataclass(slots=True)
class ConfigFSMAdapters:
    """
    Controlled I/O adapters for the FSM pipeline.

    Responsibilities:
        • Perform all necessary I/O (env loading, file resolution)
        • Parse & build Pydantic settings (impure)
        • Feed pure dicts into FSM pipeline transitions (pure)
        • DO NOT mix impurity with FSM logic
    """

    pipeline: ConfigFSMPipeline = ConfigFSMPipeline()

    # --------------------------------------------------------------------------
    # STEP 1 — Resolve environment path (impure)
    # ------------------------------------------------------------------------------
    def resolve_env_path(
        self,
        state: ConfigFSMState,
        *,
        root: str | Path | None = None,
        env_file: str | Path | None = None,
    ) -> ConfigFSMState:
        """
        Impure wrapper around env path resolution.
        Delegates all logic to env_loader.
        """
        # We do NOT load env yet, only trigger resolution
        # (env_loader will resolve base_dir and env_file)
        _ = load_env(root=root, env_file=env_file)

        return self.pipeline.step_resolve_env_path(state)

    # --------------------------------------------------------------------------
    # STEP 2 — Load environment (impure)
    # --------------------------------------------------------------------------
    def load_environment(
        self,
        state: ConfigFSMState,
        *,
        root: str | Path | None = None,
        env_file: str | Path | None = None,
    ) -> ConfigFSMState:
        """
        Impure: calls env_loader to load effective environment.
        Pure: feeds dict result into FSM.
        """
        env = load_env(root=root, env_file=env_file)

        return self.pipeline.step_load_env(
            state,
            env=env,
        )

    # --------------------------------------------------------------------------
    # STEP 3 — Construct raw settings (impure)
    # --------------------------------------------------------------------------
    def build_models(
        self,
        state: ConfigFSMState,
        *,
        env: Mapping[str, str],
    ) -> ConfigFSMState:
        """
        Impure: construct Pydantic models.
        Pure: feed dicts to FSM pipeline.
        """
        core = CoreSettings(**env)
        logging = LoggingSettings(**env)
        tracing = TracingSettings(**env)
        mt5 = MT5Settings(**env)

        settings_dict = {
            "core": core.model_dump(),
            "logging": logging.model_dump(),
            "tracing": tracing.model_dump(),
            "mt5": mt5.model_dump(),
        }

        return self.pipeline.step_build_model(
            state,
            env=env,
            settings=settings_dict,
        )

    # --------------------------------------------------------------------------
    # STEP 4 — Validate constructed models (impure)
    # --------------------------------------------------------------------------
    def validate_models(
        self,
        state: ConfigFSMState,
        *,
        env: Mapping[str, str],
        settings: Mapping[str, Any],
    ) -> ConfigFSMState:
        """
        Impure validation already done implicitly by Pydantic.
        Pure: move FSM to MODEL_VALIDATED.
        """
        return self.pipeline.step_validate_model(
            state,
            env=env,
            settings=settings,
        )

    # --------------------------------------------------------------------------
    # STEP 5 — Freeze settings (pure)
    # No I/O is required here.
    # --------------------------------------------------------------------------
    def freeze_models(
        self,
        state: ConfigFSMState,
        *,
        env: Mapping[str, str],
        settings: Mapping[str, Any],
    ) -> ConfigFSMState:
        """
        Pure step: settings are already immutable in practice.
        FSM moves to MODEL_FROZEN.
        """
        return self.pipeline.step_freeze_model(
            state,
            env=env,
            settings=settings,
        )

    # --------------------------------------------------------------------------
    # STEP 6 — READY (pure)
    # --------------------------------------------------------------------------
    def finalize_ready(
        self,
        state: ConfigFSMState,
        *,
        env: Mapping[str, str],
        settings: Mapping[str, Any],
    ) -> ConfigFSMState:
        """
        Final pure step: produce READY state.
        """
        return self.pipeline.step_ready(
            state,
            env=env,
            settings=settings,
        )
