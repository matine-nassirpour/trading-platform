from pydantic import BaseModel

from quantum.domain.events.base import BaseEvent

REGISTRY: dict[str, type[BaseModel]] = {}


def schema_key(cls: type[BaseModel]) -> str:
    """
    Derive registry key from event class metadata.
    Example: event_name="trading.order_submit", schema_version=1 -> "order_submit_v1"
    """
    base = cls.event_name.split(".")[-1]
    return f"{base}_v{cls.schema_version}"


def register(model: type[BaseModel]) -> None:
    REGISTRY[schema_key(model)] = model


def encode_event(event: BaseEvent) -> dict:
    """Single official encoding path (stable JSON)."""
    return event.model_dump(by_alias=True)


def decode_event(key: str, payload: dict) -> BaseModel:
    """Single official decoding path via registry."""
    model = REGISTRY[key]
    return model(**payload)
