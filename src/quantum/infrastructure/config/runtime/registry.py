from __future__ import annotations

from collections.abc import Mapping

from pydantic import BaseModel

from quantum.infrastructure.config.models.core import CoreSettings
from quantum.infrastructure.config.models.logging import LoggingSettings
from quantum.infrastructure.config.models.mt5 import MT5Settings
from quantum.infrastructure.config.models.tracing import TracingSettings


class ConfigModelRegistry:
    """
    Central safety-grade registry of declared configuration models.
    Used for strict routing, prefix derivation, and environment validation.
    """

    __slots__ = ("_models",)

    def __init__(self, models: Mapping[str, type[BaseModel]]) -> None:
        self._models = dict(models)

    @property
    def models(self) -> Mapping[str, type[BaseModel]]:
        return self._models


CONFIG_MODELS = ConfigModelRegistry(
    {
        "core": CoreSettings,
        "logging": LoggingSettings,
        "tracing": TracingSettings,
        "mt5": MT5Settings,
    }
)
