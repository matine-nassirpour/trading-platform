from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class BaseConfigSettings(BaseModel):
    """
    Clean, explicit, industry-grade settings base class.

    - No implicit .env loading
    - No implicit env var resolution
    - Immutable
    - Extra fields ignored
    - Case-insensitive fields (normalize keys beforehand)
    - Deterministic serialisation
    """

    model_config = ConfigDict(
        extra="ignore",  # ignore unexpected keys
        frozen=True,  # strict immutability
        arbitrary_types_allowed=False,
        validate_assignment=False,
    )
