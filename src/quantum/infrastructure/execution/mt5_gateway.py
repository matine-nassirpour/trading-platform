import logging
import signal
import time
from collections.abc import Callable
from contextlib import contextmanager
from typing import Any

from quantum.infrastructure.execution.gateway_registry import (
    is_gateway_healthy,
    record_gateway_failure,
    record_gateway_success,
)
from quantum.infrastructure.execution.mappings.mt5_retcode_map import (
    map_mt5_res_to_exec,
)
from quantum.infrastructure.observability.metrics.mt5 import (
    exec_channel_latency_ms,
    exec_channel_total,
)
from quantum.infrastructure.observability.tracing.traces import get_tracer
from quantum.shared.config.config_manager import ConfigManager
from quantum.shared.types.channels import ExecutionChannel
from quantum.shared.types.execution import ExecutionCode
from quantum.shared.types.execution_result import ExecutionResult

logger = logging.getLogger(__name__)
tracer = get_tracer("infra.execution.mt5")


# ──────────────────────────────────────────────────────────────────────────────
# Terminal init / shutdown
# ──────────────────────────────────────────────────────────────────────────────
def init_mt5_terminal(channel: ExecutionChannel, path: str | None = None) -> bool:
    """
    Initializes and logs into a MetaTrader5 terminal for the given execution channel.

    Loads credentials (login, password, server) from ConfigManager
    and attempts a secure MT5 connection.
    """
    try:
        import MetaTrader5 as mt5  # lazy import

        creds = ConfigManager.get_mt5_credentials(channel.name)
        if not creds["login"] or not creds["server"] or not creds["password"]:
            logger.error(
                f"Missing MT5 credentials for channel {channel.name}",
                extra={"attrs": {"channel": channel.name}},
            )
            return False

        ok = mt5.initialize(
            path=path,
            login=int(creds["login"]),
            password=creds["password"],
            server=creds["server"],
        )

        if not ok:
            try:
                code, msg = mt5.last_error()
                logger.error(
                    f"MT5 initialize failed for {channel.name}",
                    extra={"attrs": {"error_code": code, "error_msg": msg}},
                )
            except Exception:
                logger.error(
                    f"MT5 initialize failed (no last_error) for {channel.name}",
                    extra={"attrs": {"path": path}},
                )
        else:
            logger.info(
                f"MT5 terminal initialized for {channel.name}",
                extra={"attrs": {"server": creds["server"], "login": creds["login"]}},
            )
        return bool(ok)

    except Exception as e:
        logger.exception(
            f"MT5 init error for {channel.name}: {type(e).__name__} {e}",
            extra={"attrs": {"path": path}},
        )
        return False


def shutdown_mt5_terminal() -> None:
    """Best-effort shutdown for the MetaTrader5 terminal."""
    try:
        import MetaTrader5 as mt5  # lazy import

        mt5.shutdown()
    except Exception:
        pass


# ──────────────────────────────────────────────────────────────────────────────
# Dynamic timeout configuration
# ──────────────────────────────────────────────────────────────────────────────


def _get_exec_timeout() -> float:
    """
    Returns the execution timeout (seconds) from configuration.

    Uses `quantum_exec_timeout` defined in `ConfigManager`,
    with fallback to a safe default (5.0 seconds).
    """
    try:
        settings = ConfigManager.load()
        return settings.quantum_exec_timeout
    except Exception as e:
        logger.warning(f"Failed to read quantum_exec_timeout: {e}")
        return 5.0


@contextmanager
def _timeout(seconds: float):
    """Context manager enforcing a hard timeout (Unix only)."""

    def _handler(signum, frame):
        raise TimeoutError("MT5 execution timed out")

    signal.signal(signal.SIGALRM, _handler)
    signal.alarm(int(seconds))
    try:
        yield
    finally:
        signal.alarm(0)


# ──────────────────────────────────────────────────────────────────────────────
# Core execution with health gate + circuit breaker
# ──────────────────────────────────────────────────────────────────────────────


def execute_mt5_call(
    call: str,
    func: Callable[..., Any],
    *args,
    channel: ExecutionChannel | None = None,
    **kwargs,
) -> ExecutionResult:
    """
    Executes a MetaTrader5 API call under a fully instrumented and fault-tolerant context.

    This function acts as the canonical execution harness for all MT5 API calls.
    It provides:
      - OpenTelemetry tracing
      - Prometheus metrics (latency, total)
      - Configurable timeout via ConfigManager
      - Health gating & circuit breaker integration
      - Consistent ExecutionResult contract

    Parameters
    ----------
    call : str
        Logical name of the MT5 operation (e.g. "order_send", "positions_get").
    func : Callable[..., Any]
        The MetaTrader5 function to execute.
    channel : ExecutionChannel | None
        Execution channel (FTMO, FUNDEDNEXT, etc.)
    *args, **kwargs :
        Parameters passed directly to the MT5 API call.

    Returns
    -------
    ExecutionResult
        Standardized result object containing code, message, and payload.
    """
    start_ms = time.time() * 1000.0
    timeout_s = _get_exec_timeout()

    with tracer.start_as_current_span(f"exec.{call}") as span:
        code = ExecutionCode.FAIL
        msg = ""
        result = None

        # Health gate check
        if channel and not is_gateway_healthy(channel):
            msg = f"Execution channel {channel.name} unhealthy — call aborted."
            logger.warning(msg)
            return ExecutionResult(
                code=ExecutionCode.INTERNAL_FAIL,
                message=msg,
                payload=None,
            )

        try:
            with _timeout(timeout_s):
                result = func(*args, **kwargs)
                res_code = getattr(result, "retcode", None)
                msg = getattr(result, "comment", "") or ""
                code = map_mt5_res_to_exec(int(res_code or -1))
                record_gateway_success(channel)

        except TimeoutError:
            msg = f"MT5 call '{call}' timed out after {timeout_s:.1f}s"
            code = ExecutionCode.INTERNAL_FAIL_TIMEOUT
            record_gateway_failure(channel)
            logger.error(msg)

        except Exception as e:
            msg = f"{type(e).__name__}: {e}"
            code = ExecutionCode.INTERNAL_FAIL
            record_gateway_failure(channel)
            logger.exception(f"MT5 call '{call}' crashed")

        # ─── Observability metrics
        dur_ms = int(time.time() * 1000.0 - start_ms)
        try:
            exec_channel_latency_ms.labels(call=call).observe(dur_ms)
            exec_channel_total.labels(call=call, code=str(code)).inc()
        except Exception:
            pass

        # ─── Tracing enrichment
        span.set_attribute("exec.channel", str(channel or "unknown"))
        span.set_attribute("exec.call", call)
        span.set_attribute("exec.code", str(code))
        span.set_attribute("exec.latency_ms", dur_ms)
        span.set_attribute("exec.timeout_s", timeout_s)

        if code != ExecutionCode.OK:
            from opentelemetry.trace import Status, StatusCode

            span.set_status(Status(StatusCode.ERROR, description=str(code)))

        # ─── Structured log
        logger.info(
            "MT5 exec",
            extra={
                "attrs": {
                    "call": call,
                    "channel": str(channel),
                    "code": str(code),
                    "latency_ms": dur_ms,
                    "msg": msg[:256] if msg else None,
                }
            },
        )

        return ExecutionResult(code=code, message=msg, payload=result)
