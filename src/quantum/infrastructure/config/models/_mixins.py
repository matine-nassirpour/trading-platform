from __future__ import annotations

from collections.abc import Iterable

from quantum.infrastructure.config.security.sensitive_policy import is_sensitive_key


class PublicSettingsMixin:
    """
    Mixin providing industry-grade sanitization of configuration models.

    Features:
        - Global pattern-based sensitive-field masking
        - Local overrides via sensitive_fields()
        - Defensive, deterministic, log-safe output
    """

    # ----------------------------------------------------------------------
    # Sensitive fields handling
    # ----------------------------------------------------------------------
    @classmethod
    def sensitive_fields(cls) -> Iterable[str]:
        """
        Explicit sensitive fields declared by the model.
        Subclasses may override to add specific secrets.
        """
        return ()

    # ----------------------------------------------------------------------
    # Public dict sanitization
    # ----------------------------------------------------------------------
    def to_public_dict(self) -> dict[str, str]:
        """
        Industry-grade sanitized dict safe for logs and diagnostics.

        Rules:
            - model_dump() is used to extract raw fields.
            - All fields marked as sensitive locally are excluded.
            - All fields matching global patterns are excluded.
            - None values are removed.
            - Values converted to str for log-safety.
            - Deterministic ordering.
        """
        raw = self.model_dump()

        local_sensitive = set(self.sensitive_fields())

        public: dict[str, str] = {}

        for key, value in raw.items():
            if value is None:
                continue

            # Local explicit exclusion
            if key in local_sensitive:
                continue

            # Global pattern-based exclusion
            if is_sensitive_key(key):
                continue

            public[key] = str(value)

        return dict(sorted(public.items()))
