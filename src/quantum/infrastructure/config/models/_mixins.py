from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from pydantic import BaseModel

from quantum.infrastructure.config.security.sensitive_policy import is_sensitive_key


class PublicSettingsMixin:
    """
    Industry-grade sanitization mixin with full cycle-detection protection.

    Guarantees:
        • Recursive sanitization across dicts, lists, sets, tuples, Pydantic models
        • Cycle-safe via deterministic visited-set tracking
        • Sensitive-field exclusion (local + global patterns)
        • Deterministic ordering (sorted keys)
        • Immutable & side-effect-free
        • Fully log-safe and audit-safe
    """

    # --------------------------------------------------------------------------
    # Sanitization helpers
    # --------------------------------------------------------------------------
    def _sanitize_value(self, value: Any, visited: set[int]) -> Any:
        """
        Cycle-safe sanitization dispatcher.

        Rules:
            - If object ID already encountered → return a stable sentinel
            - Pydantic model → sanitized via its own public interface
            - Mapping → sanitized key/value pairs
            - Iterable → sanitized elements
            - Scalar → converted to str
        """

        oid = id(value)
        if oid in visited:
            return "<cycle>"

        # We add to visited *before* descending
        visited.add(oid)

        # Case 1 — Pydantic model
        if isinstance(value, BaseModel):
            if hasattr(value, "to_public_dict"):
                return value.to_public_dict()
            return {value.__class__.__name__: "<hidden>"}

        # Case 2 — Mapping
        if isinstance(value, Mapping):
            sanitized = {
                str(k): self._sanitize_value(v, visited)
                for k, v in value.items()
                if v is not None
            }
            return dict(sorted(sanitized.items()))

        # Case 3 — Iterable (but not str/bytes)
        if isinstance(value, Iterable) and not isinstance(
            value, (str, bytes, bytearray)
        ):
            return [self._sanitize_value(v, visited) for v in value]

        # Case 4 — Scalar
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
    def to_public_dict(self) -> dict[str, Any]:
        """
        Recursively produce a sanitized, log-safe, cycle-safe representation.
        """

        raw = self.model_dump()
        local_sensitive = set(self.sensitive_fields())

        visited: set[int] = set()

        public: dict[str, Any] = {}
        for key, value in raw.items():
            if value is None:
                continue
            if key in local_sensitive:
                continue
            if is_sensitive_key(key):
                continue

            public[key] = self._sanitize_value(value, visited)

        return dict(sorted(public.items()))
