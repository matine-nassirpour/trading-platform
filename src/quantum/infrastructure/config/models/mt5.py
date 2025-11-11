"""
Quantum Core Configuration Models — MT5 Settings
────────────────────────────────────────────────
Immutable schema defining broker credentials and terminal paths for
MetaTrader 5 integrations within the Quantum platform.

Responsibilities
----------------
- Define structured, validated configuration for each MT5 prop firm.
- Enforce consistency and completeness of broker credentials.
- Provide deterministic access to terminal paths and credentials.
- Remain independent of any execution or API layer.

Design Principles
-----------------
- **Single Responsibility** : declares MT5 connection schema only.
- **Clean Architecture** : pure configuration model, no side effects.
- **Immutability** : frozen model ensuring deterministic runtime use.
- **Validation by Contract** : guarantees that declared brokers are complete.
- **Extensibility** : open to new brokers or credentials without refactor.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MT5Settings(BaseModel):

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
    mt5_ftmo_terminal_path: str | None = Field(
        default=None, description="Absolute path to FTMO MetaTrader terminal executable"
    )
    mt5_fundednext_terminal_path: str | None = Field(
        default=None,
        description="Absolute path to FundedNext MetaTrader terminal executable",
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

    # --------------------------------------------------------------------------
    # Model configuration
    # --------------------------------------------------------------------------
    model_config = ConfigDict(
        extra="ignore",
        frozen=True,
    )
