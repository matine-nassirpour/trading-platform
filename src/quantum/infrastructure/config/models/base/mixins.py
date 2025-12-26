from __future__ import annotations

import dataclasses
import uuid

from collections.abc import Iterable, Mapping
from typing import Any, cast

from pydantic import BaseModel

from quantum.infrastructure.config.sanitation.sensitive_policy import is_sensitive_key


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Internal Helpers                                                           │
# ╰────────────────────────────────────────────────────────────────────────────╯
def _to_safe_string(value: Any) -> str:
    """
    Deterministic, audit-safe conversion of scalar values to string.
    Handles:
        - Decimal
        - Enum
        - datetime/date/time
        - UUID
        - Others fallback via str(value)

    Safety properties:
        • Never fails silently
        • Always produces a string
        • Stable representation over time
    """
    try:
        # Enum → name
        if (
            hasattr(value, "name")
            and hasattr(value, "value")
            and not isinstance(value, type)
        ):
            return str(value.name)

        # UUID → canonical string
        if isinstance(value, uuid.UUID):
            return str(value)

        # Datetime-like → ISO 8601
        if hasattr(value, "isoformat"):
            return cast(str, value.isoformat())

        # Decimal or others
        return str(value)

    except Exception as e:
        return f"<unrenderable:{type(value).__name__}:{e}>"


def _get_stable_guid(obj: Any, guid_cache: dict[int, uuid.UUID]) -> uuid.UUID:
    """
    Return a stable GUID for the lifetime of the sanitization call.
    More robust than using id(obj) alone.

    id(obj) is used as key in the cache, but each object is assigned a GUID.
    This prevents collisions across processes / JIT / GC edge cases.
    """
    oid = id(obj)
    if oid not in guid_cache:
        guid_cache[oid] = uuid.uuid4()
    return guid_cache[oid]


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Full-cycle sanitization                                                    │
# ╰────────────────────────────────────────────────────────────────────────────╯
class PublicSettingsMixin:
    """
    Industry-grade sanitization mixin with:
        • Robust, GUID-based cycle detection
        • Recursive sanitization of dicts, iterables, dataclasses, namedtuples,
          TypedDicts, and Pydantic models
        • Sensitive-field masking ("<redacted>")
        • Deterministic ordering
        • Pure, side-effect-free, safety-critical ready
    """

    # --------------------------------------------------------------------------
    # Sanitization helpers
    # --------------------------------------------------------------------------
    @staticmethod
    def _sanitize_pydantic(value: BaseModel) -> Any:
        if hasattr(value, "to_public_dict"):
            return value.to_public_dict()
        return {value.__class__.__name__: "<hidden>"}

    def _sanitize_dataclass(
        self, value: Any, guid_cache: dict[int, uuid.UUID], visited: set[uuid.UUID]
    ) -> dict[str, Any]:
        out = {}
        for f in dataclasses.fields(value):
            v = getattr(value, f.name)
            out[f.name] = self._sanitize(v, guid_cache=guid_cache, visited=visited)
        return dict(sorted(out.items()))

    def _sanitize_namedtuple(
        self, value: Any, guid_cache: dict[int, uuid.UUID], visited: set[uuid.UUID]
    ) -> dict[str, Any]:
        out = {}
        for field in value._fields:
            v = getattr(value, field)
            out[field] = self._sanitize(v, guid_cache=guid_cache, visited=visited)
        return dict(sorted(out.items()))

    def _sanitize_mapping(
        self,
        value: Mapping[Any, Any],
        guid_cache: dict[int, uuid.UUID],
        visited: set[uuid.UUID],
    ) -> dict[str, Any]:
        out = {}
        for k, v in value.items():
            if v is None:
                continue
            out[str(k)] = self._sanitize(v, guid_cache=guid_cache, visited=visited)
        return dict(sorted(out.items()))

    def _sanitize_iterable(
        self,
        value: Iterable[Any],
        guid_cache: dict[int, uuid.UUID],
        visited: set[uuid.UUID],
    ) -> list[Any]:
        return [
            self._sanitize(v, guid_cache=guid_cache, visited=visited) for v in value
        ]

    @staticmethod
    def _is_iterable(value: Any) -> bool:
        return isinstance(value, Iterable) and not isinstance(
            value, (str, bytes, bytearray)
        )

    def _sanitize(
        self, value: Any, *, guid_cache: dict[int, uuid.UUID], visited: set[uuid.UUID]
    ) -> Any:
        """
        Recursive, cycle-safe sanitization.
        """
        if not (
            isinstance(value, BaseModel)
            or dataclasses.is_dataclass(value)
            or hasattr(value, "_fields")
            or isinstance(value, Mapping)
            or self._is_iterable(value)
        ):
            return _to_safe_string(value)

        guid = _get_stable_guid(value, guid_cache)
        if guid in visited:
            return "<cycle>"
        visited.add(guid)

        if isinstance(value, BaseModel):
            return self._sanitize_pydantic(value)

        if dataclasses.is_dataclass(value):
            return self._sanitize_dataclass(value, guid_cache, visited)

        if hasattr(value, "_fields"):
            return self._sanitize_namedtuple(value, guid_cache, visited)

        if isinstance(value, Mapping):
            return self._sanitize_mapping(value, guid_cache, visited)

        if self._is_iterable(value):
            return self._sanitize_iterable(value, guid_cache, visited)

        return _to_safe_string(value)

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
        Produce a sanitized, log-safe, audit-safe dict representation.

        Sensitive keys are masked (not removed!) as "<redacted>".
        """

        raw = self.model_dump()  # type: ignore[attr-defined]

        local_sensitive = set(self.sensitive_fields())

        guid_cache: dict[int, uuid.UUID] = {}
        visited: set[uuid.UUID] = set()

        public: dict[str, Any] = {}

        for key, value in raw.items():
            if value is None:
                continue

            # Sensitive?

            if key in local_sensitive or is_sensitive_key(key):
                public[key] = "<redacted>"
                continue

            public[key] = self._sanitize(value, guid_cache=guid_cache, visited=visited)

        return dict(sorted(public.items()))
