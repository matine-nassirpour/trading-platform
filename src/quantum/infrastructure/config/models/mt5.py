from __future__ import annotations

from collections.abc import Iterable

from pydantic import Field, model_validator

from quantum.infrastructure.config.models.base.base_settings import BaseConfigSettings
from quantum.infrastructure.config.models.base.mixins import PublicSettingsMixin
from quantum.infrastructure.config.value_objects.executable_path_spec import (
    ExecutablePathSpec,
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
    quantum_mt5_ftmo_terminal_path: ExecutablePathSpec | None = Field(
        default=None, description="Absolute path to FTMO MetaTrader terminal executable"
    )
    quantum_mt5_fundednext_terminal_path: ExecutablePathSpec | None = Field(
        default=None,
        description="Absolute path to FundedNext MetaTrader terminal executable",
    )

    # --------------------------------------------------------------------------
    # Sensitive Fields
    # --------------------------------------------------------------------------
    @classmethod
    def sensitive_fields(cls) -> Iterable[str]:
        return (
            "quantum_mt5_ftmo_password",
            "quantum_mt5_fundednext_password",
        )

    # --------------------------------------------------------------------------
    # Validators
    # --------------------------------------------------------------------------
    @model_validator(mode="after")
    def validate_credentials(self) -> MT5Settings:
        brokers = {
            "FTMO": {
                "login": self.quantum_mt5_ftmo_login,
                "server": self.quantum_mt5_ftmo_server,
                "password": self.quantum_mt5_ftmo_password,
            },
            "FUNDEDNEXT": {
                "login": self.quantum_mt5_fundednext_login,
                "server": self.quantum_mt5_fundednext_server,
                "password": self.quantum_mt5_fundednext_password,
            },
        }

        for name, fields in brokers.items():
            values = list(fields.values())
            if any(values) and not all(values):
                missing = [k for k, v in fields.items() if v is None]
                raise ValueError(
                    f"Incomplete {name} credentials. Missing fields: {', '.join(missing)}"
                )

        return self
