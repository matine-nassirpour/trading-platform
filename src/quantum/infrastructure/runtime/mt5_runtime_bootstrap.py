"""
MT5 Runtime Bootstrap
──────────────────────────────────────────────────────────────────────────────
Responsible for initializing, monitoring, and gracefully shutting down all
MetaTrader5 terminals defined in the execution gateway registry.

Key guarantees:
- All MT5 terminals (FTMO, FundedNext, etc.) are initialized safely before order flow.
- Terminal state and connectivity are observable (metrics, traces, structured logs).
- Runtime can be safely reused in multi-prop firm setups.
- Clean shutdown registered automatically on exit.
"""

import atexit
import logging
import time

from quantum.infrastructure.execution.gateway_registry import get_gateway
from quantum.infrastructure.execution.mt5_gateway import (
    init_mt5_terminal,
    shutdown_mt5_terminal,
)
from quantum.infrastructure.observability.metrics.mt5 import terminal_up
from quantum.infrastructure.observability.tracing.traces import get_tracer
from quantum.shared.config.config_manager import ConfigManager
from quantum.shared.types.channels import ExecutionChannel

logger = logging.getLogger(__name__)
tracer = get_tracer("infra.runtime.mt5_bootstrap")


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Channel Initialization Logic                                                │
# ╰─────────────────────────────────────────────────────────────────────────────╯


def _safe_init_channel(channel: ExecutionChannel) -> bool:
    """
    Initializes a single MT5 terminal for a given execution channel,
    with retries, telemetry, and fault tolerance.

    Returns:
        bool: True if terminal initialized successfully, False otherwise.
    """
    gw = get_gateway(channel)
    path = gw.terminal_path
    settings = ConfigManager.load()

    with tracer.start_as_current_span(f"runtime.init.{channel.name}") as span:
        span.set_attribute("mt5.channel", str(channel))
        span.set_attribute("mt5.terminal_path", path or "N/A")

        for attempt in range(1, settings.quantum_exec_retries + 1):
            start = time.time()
            logger.info(
                f"[MT5] Initializing terminal for {channel.name} "
                f"(attempt {attempt}/{settings.quantum_exec_retries})",
                extra={"attrs": {"channel": channel.name, "terminal_path": path}},
            )

            ok = init_mt5_terminal(channel, path)
            dur_ms = int((time.time() - start) * 1000)
            span.set_attribute("mt5.init_latency_ms", dur_ms)

            if ok:
                terminal_up.labels(channel=channel.name).set(1.0)
                logger.info(
                    f"[MT5] Terminal initialized successfully for {channel.name} "
                    f"in {dur_ms} ms",
                    extra={"attrs": {"channel": channel.name, "latency_ms": dur_ms}},
                )
                span.set_attribute("mt5.init_status", "ok")
                return True

            # Failed attempt
            terminal_up.labels(channel=channel.name).set(0.0)
            logger.warning(
                f"[MT5] Initialization failed for {channel.name} (attempt {attempt})",
                extra={"attrs": {"channel": channel.name, "terminal_path": path}},
            )

            # Exponential backoff
            backoff = min(5.0, settings.quantum_exec_backoff * (2 ** (attempt - 1)))
            time.sleep(backoff)

        # All attempts failed
        logger.error(
            f"[MT5] Terminal initialization failed after {settings.quantum_exec_retries} attempts "
            f"for {channel.name}",
            extra={"attrs": {"channel": channel.name, "terminal_path": path}},
        )
        span.set_attribute("mt5.init_status", "failed")
        terminal_up.labels(channel=channel.name).set(0.0)
        return False


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Global Bootstrap                                                            │
# ╰─────────────────────────────────────────────────────────────────────────────╯


def bootstrap_all_terminals() -> None:
    """
    Initializes all MT5 terminals declared in the gateway registry.

    - Called once at system startup.
    - Ensures each terminal is initialized and healthy before trading begins.
    - Registers a shutdown hook for clean exit.
    """
    logger.info("Bootstrapping all MT5 execution terminals...")
    with tracer.start_as_current_span("runtime.mt5.bootstrap_all") as span:
        status_summary: dict[str, bool] = {}

        for channel in ExecutionChannel:
            try:
                ok = _safe_init_channel(channel)
                status_summary[channel.name] = ok
                if ok:
                    logger.info(f"MT5 terminal ready for {channel.name}")
                else:
                    logger.warning(
                        f"MT5 terminal bootstrap incomplete for {channel.name}"
                    )
            except Exception as e:
                logger.exception(
                    f"Unexpected error during MT5 bootstrap for {channel.name}: {e}",
                    extra={"attrs": {"channel": channel.name}},
                )
                terminal_up.labels(channel=channel.name).set(0.0)
                status_summary[channel.name] = False

        # Attach high-level summary to the trace
        span.set_attribute("mt5.bootstrap.summary", str(status_summary))

    # Register clean shutdown hook
    try:
        atexit.register(_graceful_shutdown)
        logger.info("Registered MT5 shutdown hook (atexit).")
    except Exception as e:
        logger.warning(f"Failed to register MT5 shutdown hook: {e}")


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Graceful Shutdown Logic                                                     │
# ╰─────────────────────────────────────────────────────────────────────────────╯


def _graceful_shutdown() -> None:
    """Cleanly shuts down all MT5 terminals on process exit."""
    logger.info("[MT5] Shutting down all terminals...")
    with tracer.start_as_current_span("runtime.mt5.shutdown"):
        try:
            shutdown_mt5_terminal()
            for channel in ExecutionChannel:
                terminal_up.labels(channel=channel.name).set(0.0)
            logger.info("[MT5] All terminals shut down successfully.")
        except Exception as e:
            logger.exception("[MT5] Error during shutdown", exc_info=e)
