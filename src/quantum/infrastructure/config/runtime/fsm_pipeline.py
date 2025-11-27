from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from quantum.infrastructure.config.runtime.fsm_controller import ConfigFSMController
from quantum.infrastructure.config.runtime.fsm_model import ConfigFSMState


@dataclass(slots=True)
class ConfigFSMPipeline:
    """
    Pure functional configuration pipeline.

    Responsibilities:
        • Orchestrate the FSM lifecycle
        • Enforce monotonic deterministic flow
        • Transform raw data into next FSM states
        • Never perform I/O
        • Serve as a pure core reused by the runtime ConfigManager

    This pipeline expects all I/O to be performed by upstream adapters.
    """

    controller: ConfigFSMController = ConfigFSMController()

    # --------------------------------------------------------------------------
    # Pipeline Steps
    # --------------------------------------------------------------------------
    def step_resolve_env_path(
        self,
        state: ConfigFSMState,
        *,
        metadata: dict | None = None,
    ) -> ConfigFSMState:
        """
        Pure step resolving env path (logical abstraction).
        No I/O performed here.
        """
        return self.controller.step_env_path_resolved(
            state,
            metadata=metadata,
        )

    def step_load_env(
        self,
        state: ConfigFSMState,
        *,
        env: Mapping[str, str],
        metadata: dict | None = None,
    ) -> ConfigFSMState:
        """
        Pure step loading effective environment.
        The environment MUST already be provided by an outer adapter.
        """
        return self.controller.step_env_loaded(
            state,
            env=dict(env),
            metadata=metadata,
        )

    def step_build_model(
        self,
        state: ConfigFSMState,
        *,
        env: Mapping[str, str],
        settings: Mapping[str, Any],
        metadata: dict | None = None,
    ) -> ConfigFSMState:
        """
        Pure step constructing raw config model (dict form).
        Pydantic or other parsing happens outside of this pipeline.
        """
        return self.controller.step_model_built(
            state,
            env=dict(env),
            settings=dict(settings),
            metadata=metadata,
        )

    def step_validate_model(
        self,
        state: ConfigFSMState,
        *,
        env: Mapping[str, str],
        settings: Mapping[str, Any],
        metadata: dict | None = None,
    ) -> ConfigFSMState:
        """
        Pure step validating settings.
        Assumes that validation is done externally.
        """
        return self.controller.step_model_validated(
            state,
            env=dict(env),
            settings=dict(settings),
            metadata=metadata,
        )

    def step_freeze_model(
        self,
        state: ConfigFSMState,
        *,
        env: Mapping[str, str],
        settings: Mapping[str, Any],
        metadata: dict | None = None,
    ) -> ConfigFSMState:
        """
        Pure step producing frozen model.
        All settings MUST be immutable at this point.
        """
        return self.controller.step_model_frozen(
            state,
            env=dict(env),
            settings=dict(settings),
            metadata=metadata,
        )

    def step_ready(
        self,
        state: ConfigFSMState,
        *,
        env: Mapping[str, str],
        settings: Mapping[str, Any],
        metadata: dict | None = None,
    ) -> ConfigFSMState:
        """
        Final step: READY state.
        """
        return self.controller.step_ready(
            state,
            env=dict(env),
            settings=dict(settings),
            metadata=metadata,
        )
