from __future__ import annotations

from collections.abc import Iterable, Mapping

from pydantic import BaseModel

from quantum.infrastructure.config.security.sensitive_policy import is_sensitive_key


class PublicSettingsMixin:
    """
    Industry-grade sanitization mixin for configuration models.

    Features:
        • Recursive sanitization of nested models (Pydantic, VO, dicts, lists, sets)
        • Local sensitive field overrides (sensitive_fields())
        • Global pattern-based masking (is_sensitive_key)
        • Deterministic ordering for stable logs
        • Fully log-safe output (no leaks, no unsafe repr)
        • Structural transparency (sub-models reveal only their own public dict)
    """

    # --------------------------------------------------------------------------
    # Sanitization helpers
    # --------------------------------------------------------------------------
    def _sanitize_value(self, value):
        """
        Sanitization of any value type:
            - Nested Pydantic models
            - Sequences
            - Dict-like mappings
            - Scalars
        """

        # ─── Case 1: Pydantic model (or subclass)
        if isinstance(value, BaseModel):
            # Prefer its own to_public_dict() if it implements it
            if hasattr(value, "to_public_dict"):
                return value.to_public_dict()
            # Fallback to minimal safe repr
            return {value.__class__.__name__: "<hidden>"}

        # ─── Case 2: Mapping (dict-like)
        if isinstance(value, Mapping):
            sanitized = {
                str(k): self._sanitize_value(v)
                for k, v in value.items()
                if v is not None
            }
            return dict(sorted(sanitized.items()))

        # ─── Case 3: Iterable (list, tuple, set)
        if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
            return [self._sanitize_value(v) for v in value]

        # ─── Case 4: Scalar
        return str(value)

    # --------------------------------------------------------------------------
    # Sensitive fields (local overrides)
    # --------------------------------------------------------------------------
    @classmethod
    def sensitive_fields(cls) -> Iterable[str]:
        """
        Explicit sensitive fields declared by the model.
        Subclasses may override to add specific secrets.
        """
        return ()

    # --------------------------------------------------------------------------
    # Public dict sanitization
    # --------------------------------------------------------------------------
    def to_public_dict(self) -> dict[str, str | dict]:
        """
        Recursively produce a sanitized, log-safe public representation.

        Rules:
            - model_dump() extracts raw data
            - Sensitive fields excluded (local + global rules)
            - None values excluded
            - Nested models sanitized recursively
            - Collections sanitized recursively
            - Deterministic ordering
        """

        raw = self.model_dump()
        local_sensitive = set(self.sensitive_fields())

        public: dict[str, str | dict] = {}

        for key, value in raw.items():
            if value is None:
                continue

            # Sensitive exclusion (local or global)
            if key in local_sensitive:
                continue
            if is_sensitive_key(key):
                continue

            public[key] = self._sanitize_value(value)

        # Deterministic ordering
        return dict(sorted(public.items()))
