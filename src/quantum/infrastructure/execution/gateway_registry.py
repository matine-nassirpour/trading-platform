import logging
import os
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

from quantum.infrastructure.execution.mt5_gateway import (
    execute_mt5_call,
    init_mt5_terminal,
)
from quantum.shared.types.channels import ExecutionChannel

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Gateway & Health Model
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class GatewayHealth:
    initialized: bool = False
    healthy: bool = False
    last_failure: float = 0.0
    consecutive_failures: int = 0
    cooldown_until: float = 0.0


@dataclass
class GatewayConfig:
    channel: ExecutionChannel
    func: Callable[..., object]
    terminal_path: str
    health: GatewayHealth = field(default_factory=GatewayHealth)


# ──────────────────────────────────────────────────────────────────────────────
# Registry
# ──────────────────────────────────────────────────────────────────────────────

_INIT_LOCK: Final = threading.Lock()
_GATEWAYS: dict[ExecutionChannel, GatewayConfig] = {}

_DEFAULT_PATHS: dict[ExecutionChannel, str] = {
    ExecutionChannel.FUNDEDNEXT: r"C:\Program Files\FundedNext MT5 Terminal\terminal64.exe",
    ExecutionChannel.FTMO: r"C:\Program Files\FTMO Global Markets MT5 Terminal\terminal64.exe",
}

# Circuit breaker parameters
_MAX_FAILURES: Final = 3
_COOLDOWN_SEC: Final = 30.0


def _resolve_terminal_path(channel: ExecutionChannel) -> str:
    env_key = f"MT5_TERMINAL_PATH_{channel.name.upper()}"
    path = os.getenv(env_key, _DEFAULT_PATHS[channel])
    p = Path(path)
    if not p.exists():
        logger.warning(
            f"MT5 terminal path does not exist for {channel.name}",
            extra={"attrs": {"path": path, "env_key": env_key}},
        )
    return str(p)


# ──────────────────────────────────────────────────────────────────────────────
# Gateway Registry Operations
# ──────────────────────────────────────────────────────────────────────────────


def get_gateway(channel: ExecutionChannel) -> GatewayConfig:
    """
    Returns the gateway configuration for the given channel.
    Lazily initializes if missing. Includes health gate check.
    """
    with _INIT_LOCK:
        gw = _GATEWAYS.get(channel)
        if gw is None:
            gw = GatewayConfig(
                channel=channel,
                func=execute_mt5_call,
                terminal_path=_resolve_terminal_path(channel),
            )
            _GATEWAYS[channel] = gw

        # Health gate logic
        h = gw.health
        now = time.time()
        if h.cooldown_until > now:
            raise RuntimeError(
                f"Execution channel {channel.name} in cooldown "
                f"until {time.strftime('%H:%M:%S', time.localtime(h.cooldown_until))}"
            )
        if not h.initialized:
            logger.warning(
                f"Gateway {channel.name} not initialized; attempting auto-init"
            )
            ok = init_mt5_terminal(channel, gw.terminal_path)
            h.initialized = bool(ok)
            h.healthy = bool(ok)
        return gw


# ──────────────────────────────────────────────────────────────────────────────
# Health Tracking Utilities
# ──────────────────────────────────────────────────────────────────────────────


def record_gateway_failure(channel: ExecutionChannel) -> None:
    """Registers a failure and trips the circuit breaker if threshold exceeded."""
    with _INIT_LOCK:
        gw = _GATEWAYS.get(channel)
        if not gw:
            return
        h = gw.health
        h.consecutive_failures += 1
        h.last_failure = time.time()
        if h.consecutive_failures >= _MAX_FAILURES:
            h.healthy = False
            h.cooldown_until = h.last_failure + _COOLDOWN_SEC
            logger.error(
                f"Gateway {channel.name} marked unhealthy after {h.consecutive_failures} failures. "
                f"Cooldown {_COOLDOWN_SEC}s activated."
            )


def record_gateway_success(channel: ExecutionChannel) -> None:
    """Resets the breaker on successful call."""
    with _INIT_LOCK:
        gw = _GATEWAYS.get(channel)
        if not gw:
            return
        h = gw.health
        h.consecutive_failures = 0
        h.healthy = True
        h.cooldown_until = 0.0


def is_gateway_healthy(channel: ExecutionChannel) -> bool:
    gw = _GATEWAYS.get(channel)
    if not gw:
        return False
    return gw.health.healthy and gw.health.initialized
