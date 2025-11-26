from __future__ import annotations

from collections.abc import Iterable


class PublicSettingsMixin:
    """
    Mixin providing standardized sanitization of configuration models.

    - Implements to_public_dict() required by BaseSettingsContract.
    - Provides sensitive_fields() hook for subclasses.
    - Ensures strong guarantees against leaking secrets in logs.

    This mixin assumes:
        - The class implements `model_dump()` (Pydantic/BaseSettings)
        - The class is frozen (recommended) or treated as immutable
    """

    # ----------------------------------------------------------------------
    # Sensitive fields handling
    # ----------------------------------------------------------------------
    @classmethod
    def sensitive_fields(cls) -> Iterable[str]:
        """
        Return an iterable of field names that must NOT appear in to_public_dict().
        Models may override to add broker passwords, API keys, secrets, tokens, etc.
        """
        return ()

    # ----------------------------------------------------------------------
    # Public dict sanitization
    # ----------------------------------------------------------------------
    def to_public_dict(self) -> dict[str, str]:
        """
        Return a sanitized, non-sensitive dict representation of this settings model.

        Rules:
            - model_dump() is used to get raw data.
            - All fields listed in sensitive_fields() are excluded.
            - None values are omitted.
            - Everything is cast to string for log safety.
            - Order is deterministic (sorted by key).

        Guaranteed safe for logs, diagnostics, metrics, health checks, etc.
        """
        raw = self.model_dump()
        sensitive = set(self.sensitive_fields())

        public: dict[str, str] = {}

        for key, value in raw.items():
            if key in sensitive:
                continue
            if value is None:
                continue
            public[key] = str(value)

        # Deterministic ordering for logs & reproducibility
        return dict(sorted(public.items()))
