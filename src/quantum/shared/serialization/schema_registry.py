from collections.abc import Iterable
from dataclasses import dataclass

from pydantic import BaseModel

from quantum.domain.events.base import BaseEvent

# Key → Pydantic class (event)
REGISTRY: dict[str, type[BaseModel]] = {}


# ──────────────────────────────────────────────────────────────────────────────
# Explicit exceptions
# ──────────────────────────────────────────────────────────────────────────────


class UnknownSchemaKeyError(KeyError):
    """The schema key is not known to the registry."""


class SchemaDecodeError(ValueError):
    """Decoding payload to model failed."""


# ──────────────────────────────────────────────────────────────────────────────
# Register
# ──────────────────────────────────────────────────────────────────────────────


def schema_key(cls: type[BaseModel]) -> str:
    """
    Builds the canonical key from the class metadata.
    Example: event_name="trading.order_fill", schema_version=2
    -> "trading.order_fill.v2"
    """
    try:
        name = cls.event_name  # type: ignore[attr-defined]
        ver = cls.schema_version  # type: ignore[attr-defined]
    except Exception as e:  # pragma: no cover
        raise ValueError(
            f"Class {cls} must define 'event_name' and 'schema_version'"
        ) from e
    return f"{name}.v{ver}"


def register(model: type[BaseModel]) -> None:
    """Explicitly registers an event class in the registry."""
    REGISTRY[schema_key(model)] = model


def register_event(model: type[BaseEvent]) -> type[BaseEvent]:
    """
    Self-registration decorator.

    Example:
        @register_event
        class MyEvent(BaseEvent): ...
    """
    register(model)
    return model


# ──────────────────────────────────────────────────────────────────────────────
# Key Helpers
# ──────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ParsedKey:
    namespace: str
    event: str
    version: int

    @property
    def base(self) -> str:
        return f"{self.namespace}.{self.event}"


def _parse_key(key: str) -> ParsedKey:
    """
    Parse "ns.event.vN" → (namespace='ns', event='event', version=N).
    The 'event' can contain periods (e.g., 'order_fill'); the version is
    searched for at the end in the form '.v<digits>'.
    """
    if ".v" not in key:
        raise UnknownSchemaKeyError(f"Invalid schema key (missing .v<version>): {key}")
    base, v = key.rsplit(".v", 1)
    if "." not in base:
        raise UnknownSchemaKeyError(f"Invalid schema key (missing namespace): {key}")
    if not v.isdigit():
        raise UnknownSchemaKeyError(f"Invalid schema version in key: {key}")
    namespace, event = base.split(".", 1)
    return ParsedKey(namespace=namespace, event=event, version=int(v))


def _iter_versions_for_base(base: str) -> Iterable[tuple[int, str]]:
    """
    Returns the (version, key) values available in the registry for a given 'base',
    sorted by descending version.
    """
    prefix = f"{base}.v"
    candidates = []
    for k in REGISTRY.keys():
        if k.startswith(prefix):
            try:
                pk = _parse_key(k)
                candidates.append((pk.version, k))
            except Exception:
                # ignore invalid keys
                continue
    return sorted(candidates, key=lambda x: x[0], reverse=True)


# ──────────────────────────────────────────────────────────────────────────────
# Encoding / Decoding
# ──────────────────────────────────────────────────────────────────────────────


def event_key(event: BaseEvent) -> str:
    """Schema key for an event instance."""
    return schema_key(event.__class__)


def encode_event(event: BaseEvent) -> dict:
    """
    Legacy encoding path: Returns only the JSON payload.
    Kept for backward compatibility.
    """
    return event.model_dump(by_alias=True)


def decode_event(key: str, payload: dict, *, allow_downgrade: bool = True) -> BaseEvent:
    """
    Decoding path with explicit key.
      - Attempts the exact version.
      - If allow_downgrade=True and key unknown, attempts the closest lower version
    for the *same event* (same namespace+event), otherwise raises UnknownSchemaKeyError.
    """
    try:
        model = REGISTRY[key]
        return model(**payload)  # type: ignore[call-arg]
    except KeyError:
        # Attempt version fallback if allowed
        if not allow_downgrade:
            raise UnknownSchemaKeyError(f"Unknown schema key: {key}") from None
        try:
            pk = _parse_key(key)
        except UnknownSchemaKeyError:
            raise
        # Browses available versions of the same event (desc)
        for ver, alt_key in _iter_versions_for_base(pk.base):
            if ver < pk.version:
                try:
                    model = REGISTRY[alt_key]
                    return model(**payload)  # type: ignore[call-arg]
                except Exception as e:
                    raise SchemaDecodeError(
                        f"decode failed for fallback {alt_key}: {e}"
                    ) from e
        raise UnknownSchemaKeyError(
            f"No compatible schema found for base '{pk.base}' < v{pk.version}"
        ) from None
    except Exception as e:
        raise SchemaDecodeError(f"decode failed for {key}: {e}") from e


def encode_enveloped(event: BaseEvent) -> dict:
    """
    Recommended encoding path: Returns a {key, payload} envelope.
    """
    return {
        "key": event_key(event),
        "payload": event.model_dump(by_alias=True),
    }


def decode_enveloped(envelope: dict, *, allow_downgrade: bool = True) -> BaseEvent:
    """
    Decoding an envelope {key, payload}.
    """
    try:
        key = envelope["key"]
        payload = envelope["payload"]
    except Exception as e:
        raise SchemaDecodeError(f"invalid envelope (missing key/payload): {e}") from e
    return decode_event(key, payload, allow_downgrade=allow_downgrade)
