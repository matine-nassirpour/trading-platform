from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from quantum.infrastructure.config.environment.loader import load_env_from_resolved
from quantum.infrastructure.config.environment.model_router import (
    EnvironmentModelRouter,
)
from quantum.infrastructure.config.environment.resolver import resolve_env
from quantum.infrastructure.config.environment.types import EnvResolutionResult
from quantum.infrastructure.config.models.core import CoreSettings
from quantum.infrastructure.config.models.logging import LoggingSettings
from quantum.infrastructure.config.models.mt5 import MT5Settings
from quantum.infrastructure.config.models.tracing import TracingSettings
from quantum.infrastructure.config.runtime.fsm.model import ConfigFSMState
from quantum.infrastructure.config.runtime.fsm.pipeline import ConfigFSMPipeline


@dataclass(slots=True)
class ConfigFSMAdapters:
    """
    I/O Adapters driving the FSM pipeline.

    Strict layering:
        • resolve_env(...)          → PURE (no reads)
        • load_env_from_resolved    → IMPURE (1 call only)
        • pydantic construction     → IMPURE
        • FSM transitions           → PURE

    Guaranteed:
        • No double env loading
        • No hidden I/O
        • Deterministic resolve/load split
    """

    pipeline: ConfigFSMPipeline = field(default_factory=ConfigFSMPipeline)

    # --------------------------------------------------------------------------
    # STEP 1 — Resolve environment path (impure: uses file system)
    # ------------------------------------------------------------------------------
    def resolve_env_path(
        self,
        state: ConfigFSMState,
        *,
        root: str | Path | None = None,
        env_file: str | Path | None = None,
    ) -> tuple[ConfigFSMState, EnvResolutionResult]:
        resolution = resolve_env(root=root, env_file=env_file)
        new_state = self.pipeline.step_resolve_env_path(state)
        return new_state, resolution

    # --------------------------------------------------------------------------
    # STEP 2 — Load environment (impure, called once)
    # --------------------------------------------------------------------------
    def load_environment(
        self,
        state: ConfigFSMState,
        *,
        resolution: EnvResolutionResult,
        root_param,
        env_file_param,
    ) -> ConfigFSMState:
        env = load_env_from_resolved(
            resolution,
            root_param=root_param,
            env_file_param=env_file_param,
        )
        return self.pipeline.step_load_env(state, env=env)

    # --------------------------------------------------------------------------
    # STEP 3 — Construct raw Pydantic models (impure)
    # --------------------------------------------------------------------------
    def build_models(
        self,
        state: ConfigFSMState,
        *,
        env: Mapping[str, str],
    ) -> ConfigFSMState:
        models = {
            "core": CoreSettings,
            "logging": LoggingSettings,
            "tracing": TracingSettings,
            "mt5": MT5Settings,
        }

        routed_env = EnvironmentModelRouter.route(models, env)

        # Construct each model with its own routed environment
        core = CoreSettings(**routed_env["core"])
        logging = LoggingSettings(**routed_env["logging"])
        tracing = TracingSettings(**routed_env["tracing"])
        mt5 = MT5Settings(**routed_env["mt5"])

        settings_dict = {
            "core": core.model_dump(),
            "logging": logging.model_dump(),
            "tracing": tracing.model_dump(),
            "mt5": mt5.model_dump(),
        }

        return self.pipeline.step_build_model(state, env=env, settings=settings_dict)

    # --------------------------------------------------------------------------
    # STEP 4 — Validate constructed models (already validated by Pydantic)
    # --------------------------------------------------------------------------
    def validate_models(
        self,
        state: ConfigFSMState,
        *,
        env: Mapping[str, str],
        settings: Mapping[str, Any],
    ) -> ConfigFSMState:
        return self.pipeline.step_validate_model(state, env=env, settings=settings)

    # --------------------------------------------------------------------------
    # STEP 5 — Freeze settings (pure)
    # --------------------------------------------------------------------------
    def freeze_models(
        self,
        state: ConfigFSMState,
        *,
        env: Mapping[str, str],
        settings: Mapping[str, Any],
    ) -> ConfigFSMState:
        return self.pipeline.step_freeze_model(state, env=env, settings=settings)

    # --------------------------------------------------------------------------
    # STEP 6 — Finalize READY (pure)
    # --------------------------------------------------------------------------
    def finalize_ready(
        self,
        state: ConfigFSMState,
        *,
        env: Mapping[str, str],
        settings: Mapping[str, Any],
    ) -> ConfigFSMState:
        return self.pipeline.step_ready(state, env=env, settings=settings)
