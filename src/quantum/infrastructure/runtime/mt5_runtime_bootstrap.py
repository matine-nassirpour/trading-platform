"""
MT5 Runtime Bootstrap
──────────────────────────────────────────────────────────────────────────────
Responsible for initializing, monitoring, and gracefully shutting down all
MetaTrader5 terminals defined in the execution gateway registry.

This runtime orchestrator ensures that:
- all terminals (FTMO, FundedNext, etc.) are started safely before order flow,
- terminal state and connectivity are observable through logs, metrics, and traces,
- resources are released cleanly on shutdown.

Complies with Clean Architecture: no domain or application dependency.
"""

import atexit
import logging
import time
from typing import Final

from quantum.infrastructure.execution.gateway_registry import get_gateway
from quantum.infrastructure.execution.mt5_gateway import (
    init_mt5_terminal,
    shutdown_mt5_terminal,
)
from quantum.infrastructure.observability.metrics.mt5 import terminal_up
from quantum.infrastructure.observability.tracing.traces import get_tracer
from quantum.shared.types.channels import ExecutionChannel

logger = logging.getLogger(__name__)
tracer = get_tracer("infra.runtime.mt5_bootstrap")

_MAX_INIT_RETRIES: Final = 3


def _safe_init_channel(channel: ExecutionChannel) -> bool:
    """
    Initializes a single MT5 terminal for a given execution channel,
    with retries, telemetry, and fault tolerance.
    """
    gw = get_gateway(channel)
    path = gw.get("terminal_path")

    with tracer.start_as_current_span(f"runtime.init.{channel.name}") as span:
        span.set_attribute("mt5.channel", str(channel))
        span.set_attribute("mt5.terminal_path", path or "N/A")

        for attempt in range(1, _MAX_INIT_RETRIES + 1):
            logger.info(
                f"[MT5] Initializing terminal for {channel.name} (attempt {attempt}/{_MAX_INIT_RETRIES})",
                extra={"channel": channel.name, "terminal_path": path},
            )
            start = time.time()

            ok = init_mt5_terminal(channel, path)
            dur_ms = int((time.time() - start) * 1000)
            span.set_attribute("mt5.init_latency_ms", dur_ms)

            if ok:
                logger.info(
                    f"[MT5] Terminal initialized successfully for {channel.name} in {dur_ms} ms",
                    extra={"channel": channel.name, "terminal_path": path},
                )
                terminal_up.set(1.0)
                return True

            logger.warning(
                f"[MT5] Initialization failed for {channel.name} (attempt {attempt})",
                extra={"channel": channel.name, "terminal_path": path},
            )
            terminal_up.set(0.0)
            backoff = min(5.0, 0.5 * (2 ** (attempt - 1)))
            time.sleep(backoff)

        logger.error(
            f"[MT5] Terminal initialization failed after {_MAX_INIT_RETRIES} attempts for {channel.name}",
            extra={"channel": channel.name, "terminal_path": path},
        )
        span.set_attribute("mt5.init_status", "failed")
        return False


def bootstrap_all_terminals() -> None:
    """
    Initializes all MT5 terminals declared in the gateway registry.

    - Called once at system startup.
    - Ensures each terminal is initialized and healthy before trading begins.
    - Registers a shutdown hook to close all terminals cleanly at exit.
    """
    logger.info("Bootstrapping all MT5 execution terminals...")
    with tracer.start_as_current_span("runtime.mt5.bootstrap_all"):
        for channel in ExecutionChannel:
            try:
                ok = _safe_init_channel(channel)
                if not ok:
                    logger.error(f"MT5 terminal bootstrap failed for {channel.name}")
                else:
                    logger.info(f"MT5 terminal ready for {channel.name}")
            except Exception as e:
                logger.exception(
                    f"Unexpected error during MT5 bootstrap for {channel.name}",
                    exc_info=e,
                )
                terminal_up.set(0.0)

    # Ensure graceful shutdown
    try:
        atexit.register(_graceful_shutdown)
    except Exception as e:
        logger.warning(f"Failed to register MT5 shutdown hook: {e}")


def _graceful_shutdown() -> None:
    """
    Cleanly shuts down all MT5 terminals on process exit.
    """
    logger.info("[MT5] Shutting down all terminals...")
    with tracer.start_as_current_span("runtime.mt5.shutdown"):
        try:
            shutdown_mt5_terminal()
            terminal_up.set(0.0)
            logger.info("[MT5] All terminals shut down successfully")
        except Exception as e:
            logger.exception("[MT5] Error during shutdown", exc_info=e)
