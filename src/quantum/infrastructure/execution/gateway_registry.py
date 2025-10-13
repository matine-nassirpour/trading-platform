import logging
import os

from quantum.infrastructure.execution.mt5_gateway import (
    execute_mt5_call,
    init_mt5_terminal,
)
from quantum.shared.types.channels import ExecutionChannel

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Gateway registry
# ──────────────────────────────────────────────────────────────────────────────

_FUNDEDNEXT_PATH = os.getenv(
    "MT5_TERMINAL_PATH_FUNDEDNEXT",
    r"C:\Program Files\FundedNext MT5 Terminal\terminal64.exe",  # fallback
)

_FTMO_PATH = os.getenv(
    "MT5_TERMINAL_PATH_FTMO",
    r"C:\Program Files\FTMO Global Markets MT5 Terminal\terminal64.exe",  # fallback
)

_GATEWAYS = {
    ExecutionChannel.FUNDEDNEXT: {
        "func": execute_mt5_call,
        "terminal_path": _FUNDEDNEXT_PATH,
    },
    ExecutionChannel.FTMO: {
        "func": execute_mt5_call,
        "terminal_path": _FTMO_PATH,
    },
}


def get_gateway(channel: ExecutionChannel):
    """Returns the execution gateway configuration for the given channel."""
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
    for channel, gw in _GATEWAYS.items():
        term_path = gw.get("terminal_path")
        try:
            ok = init_mt5_terminal(channel, term_path)
            if not ok:
                logger.warning(
                    f"⚠️  Failed to initialize MT5 terminal for {channel.name}",
                    extra={"attrs": {"terminal_path": term_path}},
                )
            else:
                logger.info(
                    f"✅ MT5 terminal initialized for {channel.name}",
                    extra={"attrs": {"terminal_path": term_path}},
                )
        except Exception as e:
            logger.exception(
                f"MT5 terminal initialization crashed for {channel.name}: {e}",
                extra={"attrs": {"terminal_path": term_path}},
            )


# Run initialization on module import (lazy + safe)
_initialize_gateways()
