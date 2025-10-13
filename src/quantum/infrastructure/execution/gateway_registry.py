import logging
import os
import threading
from pathlib import Path
from typing import Final

from quantum.infrastructure.execution.mt5_gateway import (
    execute_mt5_call,
    init_mt5_terminal,
)
from quantum.shared.types.channels import ExecutionChannel

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Gateway registry
# ──────────────────────────────────────────────────────────────────────────────

_INIT_LOCK: Final = threading.Lock()
_GATEWAYS: dict[ExecutionChannel, dict[str, object]] = {}

_DEFAULT_PATHS: dict[ExecutionChannel, str] = {
    ExecutionChannel.FUNDEDNEXT: r"C:\Program Files\FundedNext MT5 Terminal\terminal64.exe",
    ExecutionChannel.FTMO: r"C:\Program Files\FTMO Global Markets MT5 Terminal\terminal64.exe",
}


def _resolve_terminal_path(channel: ExecutionChannel) -> str:
    """
    Resolves the MT5 terminal path for the given channel from environment variables
    or falls back to a known default path. Validates existence if possible.
    """
    env_key = f"MT5_TERMINAL_PATH_{channel.name.upper()}"
    path = os.getenv(env_key, _DEFAULT_PATHS[channel])
    p = Path(path)

    if not p.exists():
        logger.warning(
            f"MT5 terminal path does not exist for {channel.name}",
            extra={"attrs": {"path": path, "env_key": env_key}},
        )
    else:
        logger.debug(
            f"Resolved MT5 terminal path for {channel.name}",
            extra={"attrs": {"path": path}},
        )
    return str(p)


def _register_default_gateways() -> None:
    """Initializes the gateway registry with safe defaults."""
    with _INIT_LOCK:
        for channel in ExecutionChannel:
            if channel not in _GATEWAYS:
                _GATEWAYS[channel] = {
                    "func": execute_mt5_call,
                    "terminal_path": _resolve_terminal_path(channel),
                    "initialized": False,
                }


def get_gateway(channel: ExecutionChannel) -> dict[str, object]:
    """
    Returns the gateway configuration for the given channel.
    Automatically registers defaults if not present.

    Returns a dict with keys:
      - 'func': the callable for execution
      - 'terminal_path': the MT5 executable path
      - 'initialized': bool flag (set once MT5 is connected)
    """
    with _INIT_LOCK:
        if channel not in _GATEWAYS:
            logger.warning(
                f"Gateway not found for {channel.name}; registering fallback"
            )
            _GATEWAYS[channel] = {
                "func": execute_mt5_call,
                "terminal_path": _resolve_terminal_path(channel),
                "initialized": False,
            }
        return _GATEWAYS[channel]


# ──────────────────────────────────────────────────────────────────────────────
# Lazy-safe initialization of MT5 terminals
# ──────────────────────────────────────────────────────────────────────────────


def _initialize_gateways() -> None:
    """
    Initializes all configured MT5 terminals at import time.

    Each gateway is initialized with its dedicated credentials
    and executable path. Failures are logged but not raised,
    to allow the rest of the app to start (degraded mode).
    """
    _register_default_gateways()

    for channel, gw in _GATEWAYS.items():
        term_path = gw.get("terminal_path")
        try:
            ok = init_mt5_terminal(channel, term_path)
            gw["initialized"] = bool(ok)
            if not ok:
                logger.warning(
                    f"Failed to initialize MT5 terminal for {channel.name}",
                    extra={"attrs": {"terminal_path": term_path}},
                )
            else:
                logger.info(
                    f"MT5 terminal initialized for {channel.name}",
                    extra={"attrs": {"terminal_path": term_path}},
                )
        except Exception as e:
            logger.exception(
                f"MT5 terminal initialization crashed for {channel.name}: {e}",
                extra={"attrs": {"terminal_path": term_path}},
            )


def refresh_gateway_registry() -> None:
    """
    Rebuilds the gateway registry dynamically (useful if environment changes).
    Safe to call at runtime.
    """
    logger.info("Refreshing MT5 gateway registry...")
    with _INIT_LOCK:
        _GATEWAYS.clear()
        _register_default_gateways()
    _initialize_gateways()


# Run initialization on module import (lazy + safe)
_initialize_gateways()
