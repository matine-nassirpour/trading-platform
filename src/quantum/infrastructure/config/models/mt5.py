from __future__ import annotations

from pydantic import Field, model_validator

from quantum.infrastructure.config.models._base_settings import BaseConfigSettings
from quantum.infrastructure.config.models._mixins import PublicSettingsMixin
from quantum.infrastructure.config.value_objects.executable_path import (
    ExecutablePathConfig,
)


class MT5Settings(BaseConfigSettings, PublicSettingsMixin):

    # --------------------------------------------------------------------------
    # FTMO
    # --------------------------------------------------------------------------
    quantum_mt5_ftmo_login: int | None = Field(None)
    quantum_mt5_ftmo_server: str | None = Field(None)
    quantum_mt5_ftmo_password: str | None = Field(None)

    # --------------------------------------------------------------------------
    # FundedNext
    # --------------------------------------------------------------------------
    quantum_mt5_fundednext_login: int | None = Field(None)
    quantum_mt5_fundednext_server: str | None = Field(None)
    quantum_mt5_fundednext_password: str | None = Field(None)

    # --------------------------------------------------------------------------
    # Terminal paths
    # --------------------------------------------------------------------------
    mt5_ftmo_terminal_path: ExecutablePathConfig | None = Field(
        default=None, description="Absolute path to FTMO MetaTrader terminal executable"
    )
    mt5_fundednext_terminal_path: ExecutablePathConfig | None = Field(
        default=None,
        description="Absolute path to FundedNext MetaTrader terminal executable",
    )

    # --------------------------------------------------------------------------
    # Sensitive Fields
    # --------------------------------------------------------------------------
    @classmethod
    def sensitive_fields(cls):
        return (
            "quantum_mt5_ftmo_password",
            "quantum_mt5_fundednext_password",
        )

    # --------------------------------------------------------------------------
    # Validators
    # --------------------------------------------------------------------------
    @model_validator(mode="after")
    def validate_credentials(self) -> MT5Settings:
        """Ensure that any declared broker has a complete credential set."""
        brokers = {
            "FTMO": [
                self.quantum_mt5_ftmo_login,
                self.quantum_mt5_ftmo_server,
                self.quantum_mt5_ftmo_password,
            ],
            "FUNDEDNEXT": [
                self.quantum_mt5_fundednext_login,
                self.quantum_mt5_fundednext_server,
                self.quantum_mt5_fundednext_password,
            ],
        }

        for name, values in brokers.items():
            if any(values) and not all(values):
                raise ValueError(f"Incomplete {name} broker credentials")

        return self
