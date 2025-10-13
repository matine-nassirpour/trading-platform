import logging
import time

from quantum.infrastructure.observability.metrics.mt5 import (
    exec_channel_latency_ms,
    exec_channel_total,
)
from quantum.infrastructure.observability.tracing.traces import get_tracer
from quantum.shared.config.env_loader import get_mt5_credentials
from quantum.shared.types.channels import ExecutionChannel
from quantum.shared.types.execution import ExecutionCode
from quantum.shared.types.execution_result import ExecutionResult

logger = logging.getLogger(__name__)
tracer = get_tracer("infra.execution.mt5")


# ──────────────────────────────────────────────────────────────────────────────
# Terminal init/shutdown (lazy import to avoid hard dep at import time)
# ──────────────────────────────────────────────────────────────────────────────
def init_mt5_terminal(channel: ExecutionChannel, path: str | None = None) -> bool:
    """
    Initializes and logs into a MetaTrader5 terminal for the given execution channel.

    This function loads credentials (login, password, server) from environment variables
    and performs a secure MT5 connection.

    Returns True if successfully connected, False otherwise.
    """
    try:
        import MetaTrader5 as mt5  # lazy import

        creds = get_mt5_credentials(channel.name)
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
                f"✅ MT5 terminal initialized for {channel.name}",
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
        # keep silent on shutdown
        pass


# ──────────────────────────────────────────────────────────────────────────────
# Canonical mapping
# ──────────────────────────────────────────────────────────────────────────────

MT5_RES_TO_EXEC: dict[int, ExecutionCode] = {
    1: ExecutionCode.OK,  # RES_S_OK
    -1: ExecutionCode.FAIL,  # RES_E_FAIL
    -2: ExecutionCode.INVALID_PARAMS,
    -3: ExecutionCode.NO_MEMORY,
    -4: ExecutionCode.NOT_FOUND,
    -5: ExecutionCode.INVALID_VERSION,
    -6: ExecutionCode.AUTH_FAILED,
    -7: ExecutionCode.UNSUPPORTED,
    -8: ExecutionCode.AUTO_TRADING_DISABLED,
    -10000: ExecutionCode.INTERNAL_FAIL,
    -10001: ExecutionCode.INTERNAL_FAIL_SEND,
    -10002: ExecutionCode.INTERNAL_FAIL_RECEIVE,
    -10003: ExecutionCode.INTERNAL_FAIL_INIT,
    -10004: ExecutionCode.INTERNAL_FAIL_CONNECT,
    -10005: ExecutionCode.INTERNAL_FAIL_TIMEOUT,
}


def map_mt5_res_to_exec(code: int) -> ExecutionCode:
    """Returns the canonical execution code."""
    return MT5_RES_TO_EXEC.get(code, ExecutionCode.FAIL)


# ──────────────────────────────────────────────────────────────────────────────
# Instrumented execution
# ──────────────────────────────────────────────────────────────────────────────


def execute_mt5_call(
    call: str, func, channel: ExecutionChannel | None = None, *args, **kwargs
) -> ExecutionResult:
    """
    Executes a MetaTrader5 API call under a fully instrumented and fault-tolerant context.

    This function acts as the canonical "execution harness" for all MT5 API calls.
    It wraps the raw MetaTrader5 Python API to ensure consistent behavior, observability,
    and resilience across the trading infrastructure.

    Responsibilities:
    -----------------
    - Centralizes all interactions with the MT5 Python API (e.g. `mt5.order_send`, `mt5.positions_get`).
    - Automatically instruments each call with OpenTelemetry tracing (`exec.<call>` span).
    - Records Prometheus metrics for latency and result code distribution.
    - Normalizes native MT5 result codes (`retcode`) into internal stable enum values (`ExecutionCode`).
    - Captures and logs exceptions without letting MT5 or network errors propagate.
    - Provides a unified return contract `(code, message, result)` for upper layers.

    Parameters
    ----------
    call : str
        Logical name of the MT5 operation (e.g. "order_send", "order_check").
        Used as both tracing span name and metrics label.
    func : Callable
        The MT5 API function to invoke (typically from the `MetaTrader5` module).
    channel : ExecutionChannel | None
        Logical execution channel identifier (e.g., `ExecutionChannel.FTMO`, `ExecutionChannel.FUNDEDNEXT`).
        Used for distributed tracing and metrics labeling.
        If omitted, the call is recorded under a generic `"unknown"` channel label.
    *args, **kwargs :
        Positional and keyword arguments passed directly to the MT5 function.

    Returns
    -------
    ExecutionResult
        Returns a standardized ExecutionResult dataclass.

    Notes
    -----
    - This function must **never** import or depend on domain-level abstractions.
      It belongs strictly to the infrastructure layer.
    - All error handling, logging, and telemetry concerns are managed internally.
    - The result normalization is designed to be stable across MetaTrader5 API changes.
    - Upstream layers (Application / Domain) should not interact with `MetaTrader5` directly,
      but only through this function.

    Example
    -------
    >>> from quantum.infrastructure.execution.mt5_gateway import execute_mt5_call, ExecutionCode
    >>> import MetaTrader5 as mt5
    >>> request = {...}
    >>> code, msg, result = execute_mt5_call("order_send", mt5.order_send, request)
    >>> if code is ExecutionCode.OK:
    ...     print("Order sent successfully")
    ... else:
    ...     print(f"Order failed: {code} ({msg})")
    """
    start = time.time() * 1000.0
    with tracer.start_as_current_span(f"exec.{call}") as span:
        code = ExecutionCode.FAIL
        msg = ""
        result = None

        try:
            # Actual call (provided by MT5 binding)
            result = func(*args, **kwargs)
            res_code = getattr(result, "retcode", None) if result is not None else None
            msg = getattr(result, "comment", "") if result is not None else ""

            code = map_mt5_res_to_exec(int(res_code or -1))

            # Tracing attributes
            span.set_attribute("exec.channel", str(channel or "unknown"))
            span.set_attribute("exec.call", call)
            span.set_attribute("exec.code", str(code))
            span.set_attribute("mt5.res_code", res_code)
            span.set_attribute("mt5.detail", msg)

            # Mark failed spans explicitly
            if code != ExecutionCode.OK:
                from opentelemetry.trace import Status, StatusCode

                span.set_status(Status(StatusCode.ERROR, description=str(code)))

        except Exception as e:
            msg = f"{type(e).__name__}: {e}"
            code = ExecutionCode.INTERNAL_FAIL
            from opentelemetry.trace import Status, StatusCode

            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, description=type(e).__name__))
            logger.exception(f"MT5 call {call} raised an exception")

        finally:
            dur_ms = int(time.time() * 1000.0 - start)
            span.set_attribute("exec.latency_ms", dur_ms)
            _record_metrics(call, code, dur_ms)
            logger.info(
                "MT5 exec",
                extra={
                    "attrs": {
                        "call": call,
                        "code": str(code),
                        "latency_ms": dur_ms,
                        "msg": msg[:256] if msg else None,
                    }
                },
            )

    return ExecutionResult(code=code, message=msg, payload=result)


# ──────────────────────────────────────────────────────────────────────────────
# Metrics
# ──────────────────────────────────────────────────────────────────────────────


def _record_metrics(call: str, code: ExecutionCode, latency_ms: int) -> None:
    """
    Records MT5 metrics if Prometheus is initialized.
    (Silent if metrics are not available.)
    """
    try:
        exec_channel_total.labels(call=call, code=str(code)).inc()
        exec_channel_latency_ms.labels(call=call).observe(latency_ms)
    except Exception:
        pass
