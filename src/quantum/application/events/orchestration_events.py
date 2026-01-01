"""
Application Orchestration Events
────────────────────────────────
Event definitions emitted by the application orchestrator and
transported through the configured EventBusPort abstraction.

These events are agnostic of the transport layer (asyncio, Kafka, etc.).
"""

from dataclasses import dataclass
from typing import Any

from quantum.application.types.execution_channel import ExecutionChannel


@dataclass(frozen=True)
class ExecutionStartedEvent:
    channel: ExecutionChannel
    request_id: str
    symbol: str
    action: str
    volume: float


@dataclass(frozen=True)
class ExecutionCompletedEvent:
    channel: ExecutionChannel
    request_id: str
    code: str
    message: str
    latency_ms: int
    payload: dict[str, Any] | None = None


@dataclass(frozen=True)
class ExecutionFailedEvent:
    channel: ExecutionChannel
    request_id: str
    error: str
    cause: str | None = None
