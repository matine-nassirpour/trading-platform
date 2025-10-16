import logging
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Final

from quantum.infrastructure.execution.contracts import ExecutionFunctionProtocol
from quantum.infrastructure.execution.mt5_gateway import (
    Mt5ExecutionFunction,
    init_mt5_terminal,
)
from quantum.shared.config.config_manager import ConfigManager
from quantum.shared.types.channels import ExecutionChannel

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Gateway & Health Models
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class GatewayHealth:
    """Health state for a single execution gateway."""

    initialized: bool = False
    healthy: bool = False
    last_failure: float = 0.0
    consecutive_failures: int = 0
    cooldown_until: float = 0.0

    def is_in_cooldown(self) -> bool:
        return time.time() < self.cooldown_until

    def reset(self) -> None:
        self.initialized = True
        self.healthy = True
        self.consecutive_failures = 0
        self.cooldown_until = 0.0


@dataclass
class GatewayConfig:
    """
    Canonical configuration for an execution gateway.

    Each execution channel (FTMO, FUNDEDNEXT, etc.) has:
      - a callable `func` conforming to `ExecutionFunctionProtocol`
      - a specific terminal path (inferred from env or default)
      - an independent health tracker
    """

    channel: ExecutionChannel
    func: ExecutionFunctionProtocol
    terminal_path: str
    health: GatewayHealth = field(default_factory=GatewayHealth)

    def as_dict(self) -> dict[str, object]:
        return {
            "channel": self.channel.name,
            "terminal_path": self.terminal_path,
            "health": asdict(self.health),
        }


# ──────────────────────────────────────────────────────────────────────────────
# Registry
# ──────────────────────────────────────────────────────────────────────────────

_INIT_LOCK: Final = threading.Lock()
_GATEWAYS: dict[ExecutionChannel, GatewayConfig] = {}

# Default installation paths (may be overridden by env vars)
_DEFAULT_PATHS: dict[ExecutionChannel, str] = {
    ExecutionChannel.FUNDEDNEXT: r"C:\Program Files\FundedNext MT5 Terminal\terminal64.exe",
    ExecutionChannel.FTMO: r"C:\Program Files\FTMO Global Markets MT5 Terminal\terminal64.exe",
}

# Circuit breaker parameters
_MAX_FAILURES: Final = 3
_COOLDOWN_SEC: Final = 30.0

# Global execution function (canonical)
_EXEC_FUNC: Final = Mt5ExecutionFunction()


# ──────────────────────────────────────────────────────────────────────────────
# Path Resolution
# ──────────────────────────────────────────────────────────────────────────────


def _resolve_terminal_path(channel: ExecutionChannel) -> str:
    """
    Resolves the MetaTrader5 terminal path for the given execution channel.

    Priority:
      1. ConfigManager (env or settings file): mt5_terminal_path_<CHANNEL>
      2. Default path from _DEFAULT_PATHS fallback

    Returns:
        str: absolute path to the MT5 terminal (may not exist physically)
    """
    try:
        settings = ConfigManager.load()
        attr_name = f"mt5_terminal_path_{channel.name.lower()}"
        configured_path = getattr(settings, attr_name, None)

        if configured_path:
            path = Path(configured_path)
            if not path.exists():
                logger.warning(
                    f"Configured MT5 terminal path not found for {channel.name}",
                    extra={"attrs": {"path": str(path), "source": "ConfigManager"}},
                )
            return str(path.resolve())

    except Exception as e:
        logger.warning(
            f"Failed to read terminal path from ConfigManager for {channel.name}: {e}"
        )

    # ─── Fallback to default path ──────────────────────────────────────────────
    default_path = _DEFAULT_PATHS.get(channel)
    p = Path(default_path) if default_path else Path()

    if not p.exists():
        logger.warning(
            f"Default MT5 terminal path does not exist for {channel.name}",
            extra={"attrs": {"path": str(p), "source": "default"}},
        )

    return str(p.resolve())


# ──────────────────────────────────────────────────────────────────────────────
# Gateway Registry Operations
# ──────────────────────────────────────────────────────────────────────────────


def get_gateway(channel: ExecutionChannel) -> GatewayConfig:
    """
    Returns (and lazily initializes) the gateway configuration for a given channel.

    Handles
    -------
    - Lazy initialization
    - Health gate enforcement
    - Circuit-breaker cooldowns
    """
    with _INIT_LOCK:
        gw = _GATEWAYS.get(channel)

        # ─── Lazy initialization
        if gw is None:
            gw = GatewayConfig(
                channel=channel,
                func=_EXEC_FUNC,
                terminal_path=_resolve_terminal_path(channel),
            )
            _GATEWAYS[channel] = gw
            logger.info(f"Registered gateway for {channel.name}")

        # ─── Health gate enforcement
        h = gw.health
        now = time.time()

        if h.cooldown_until > now:
            raise RuntimeError(
                f"Execution channel {channel.name} in cooldown "
                f"until {time.strftime('%H:%M:%S', time.localtime(h.cooldown_until))}"
            )

        if not h.initialized:
            logger.warning(
                f"Gateway {channel.name} not initialized; attempting auto-init..."
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
                f"[Gateway:{channel.name}] marked unhealthy after "
                f"{h.consecutive_failures} failures — cooldown {_COOLDOWN_SEC}s."
            )


def record_gateway_success(channel: ExecutionChannel) -> None:
    """Resets the circuit breaker on successful call."""
    with _INIT_LOCK:
        gw = _GATEWAYS.get(channel)
        if not gw:
            return

        h = gw.health
        h.reset()
        logger.debug(f"[Gateway:{channel.name}] health reset on success.")


def is_gateway_healthy(channel: ExecutionChannel) -> bool:
    """Returns True if the given gateway is initialized and healthy."""
    gw = _GATEWAYS.get(channel)
    if not gw:
        return False
    h = gw.health
    return h.initialized and h.healthy and not h.is_in_cooldown()
