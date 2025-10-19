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

# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Gateway & Health Models                                                     │
# ╰─────────────────────────────────────────────────────────────────────────────╯


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


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Registry                                                                    │
# ╰─────────────────────────────────────────────────────────────────────────────╯

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


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Path Resolution                                                             │
# ╰─────────────────────────────────────────────────────────────────────────────╯


def _resolve_terminal_path(channel: ExecutionChannel) -> str:
    """
    Resolves the MetaTrader5 terminal path for the given execution channel.

    Priority:
      1. Explicit config via ConfigManager (supports both naming conventions)
      2. Default path from _DEFAULT_PATHS
      3. Returns an empty Path if unresolved (never crashes)

    Ensures:
      - Compatibility with mt5_<channel>_terminal_path and mt5_terminal_path_<channel>
      - Observability of resolution process
      - Graceful degradation with warning logs
    """
    settings = None
    primary_attr: str | None = None
    secondary_attr: str | None = None
    path_candidate: Path | None = None

    try:
        settings = ConfigManager.load()
    except Exception as e:
        logger.warning(
            f"Failed to load ConfigManager while resolving MT5 path: {e}",
            exc_info=False,
        )

    if settings:
        # Primary convention: mt5_<channel>_terminal_path
        primary_attr = f"mt5_{channel.name.lower()}_terminal_path"
        # Secondary convention (legacy): mt5_terminal_path_<channel>
        secondary_attr = f"mt5_terminal_path_{channel.name.lower()}"

        for attr_name in (primary_attr, secondary_attr):
            configured_path = getattr(settings, attr_name, None)
            if configured_path:
                path_candidate = Path(configured_path)
                source = f"ConfigManager:{attr_name}"

                if not path_candidate.exists():
                    logger.warning(
                        f"Configured MT5 terminal path not found for {channel.name}",
                        extra={
                            "attrs": {"path": str(path_candidate), "source": source}
                        },
                    )
                else:
                    logger.debug(
                        f"MT5 terminal path resolved via {source}",
                        extra={"attrs": {"path": str(path_candidate)}},
                    )
                break  # First match wins

    # ─── Fallback to default paths
    if not path_candidate:
        default_path = _DEFAULT_PATHS.get(channel)
        if default_path:
            path_candidate = Path(default_path)
            source = "default"
            if not path_candidate.exists():
                logger.warning(
                    f"Default MT5 terminal path does not exist for {channel.name}",
                    extra={"attrs": {"path": str(path_candidate), "source": source}},
                )
            else:
                logger.info(
                    f"MT5 terminal path resolved from default for {channel.name}",
                    extra={"attrs": {"path": str(path_candidate)}},
                )
        else:
            # No default path defined → graceful degradation
            logger.error(
                f"No terminal path configured for channel {channel.name} "
                f"(checked {primary_attr}, {secondary_attr})",
                extra={"attrs": {"channel": channel.name}},
            )
            path_candidate = Path()

    # Normalize absolute path (safe even if nonexistent)
    return str(path_candidate.resolve())


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Gateway Registry Operations                                                 │
# ╰─────────────────────────────────────────────────────────────────────────────╯


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


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Health Tracking Utilities                                                   │
# ╰─────────────────────────────────────────────────────────────────────────────╯


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
