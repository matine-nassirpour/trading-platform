import os
from typing import Final

from prometheus_client import Counter, Gauge, Histogram

# ──────────────────────────────────────────────────────────────────────────────
# Configuration (anti-cardinality)
# ──────────────────────────────────────────────────────────────────────────────
_ENABLE_ERROR_CODE_METRIC: Final = os.getenv(
    "QUANTUM_MT5_ENABLE_ERROR_CODE_METRIC", "0"
).strip() in {"1", "true", "yes", "on"}


def _parse_allowlist(env: str | None) -> set[str]:
    if not env:
        return set()
    out: set[str] = set()
    for tok in env.split(","):
        t = tok.strip()
        if not t:
            continue
        out.add(str(int(t)) if t.isdigit() else t)
    return out


_ERROR_CODE_ALLOWLIST: Final = _parse_allowlist(
    os.getenv("QUANTUM_MT5_ERROR_CODE_ALLOWLIST", "")
)


# ──────────────────────────────────────────────────────────────────────────────
# MT5 Metrics
# ──────────────────────────────────────────────────────────────────────────────
_METRIC_PREFIX = "quantum_mt5_"
_S: Final = (0.002, 0.005, 0.01, 0.025, 0.05, 0.1, 0.2, 0.4, 0.8, 1.6, 3.2, 6.4)

# Latencies
order_check_latency_seconds = Histogram(
    f"{_METRIC_PREFIX}order_check_latency_seconds",
    "Latency of OrderCheck in seconds",
    buckets=_S,
)
order_send_latency_seconds = Histogram(
    f"{_METRIC_PREFIX}order_send_latency_seconds",
    "Latency of OrderSend in seconds",
    buckets=_S,
)
time_to_fill_seconds = Histogram(
    f"{_METRIC_PREFIX}time_to_fill_seconds",
    "Time from submit to fill in seconds",
    buckets=_S + (12.8, 25.6),
)
intent_to_ack_seconds = Histogram(
    f"{_METRIC_PREFIX}intent_to_ack_seconds",
    "Time from intent emission to broker ACK in seconds",
    buckets=_S + (12.8,),
)

# Execution quality
requotes_total = Counter(
    f"{_METRIC_PREFIX}requotes_total", "Total requotes", ["symbol"]
)

# We keep the metric by error CLASS (stable)
order_reject_class_total = Counter(
    f"{_METRIC_PREFIX}order_reject_class_total",
    "Total order rejects by error class",
    ["symbol", "error_class"],
)

# Optional: metric by exact code (high cardinality) → opt-in & bounded
if _ENABLE_ERROR_CODE_METRIC:
    order_reject_total = Counter(
        f"{_METRIC_PREFIX}order_reject_total",
        "Total order rejects by exact error code (bounded via allowlist or 'other')",
        ["error_code"],
    )
else:

    class _NoopChild:
        @staticmethod
        def inc(*_args, **_kwargs):  # noqa: D401
            return None

    class _NoopCounter:
        @staticmethod
        def labels(*_args, **_kwargs):
            return _NoopChild()

    order_reject_total = _NoopCounter()  # type: ignore
partial_fills_total = Counter(
    f"{_METRIC_PREFIX}partial_fills_total", "Total partial fills"
)

slippage_points = Histogram(
    f"{_METRIC_PREFIX}slippage_points",
    "Observed slippage in points",
    buckets=(0.1, 0.2, 0.5, 1, 2, 5, 10),
)

# Terminal health
terminal_up = Gauge(f"{_METRIC_PREFIX}terminal_up", "Terminal health 0/1")
account_free_margin = Gauge(f"{_METRIC_PREFIX}account_free_margin", "Free margin")
connection_status = Gauge(
    f"{_METRIC_PREFIX}connection_status", "Connection: 0=down,1=up,2=degraded"
)
tick_staleness_seconds = Histogram(
    f"{_METRIC_PREFIX}tick_staleness_seconds",
    "Market data staleness in seconds",
    buckets=(0.1, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0),
)

# Flow
intents_total = Counter(f"{_METRIC_PREFIX}intents_total", "Total trade intents")
orders_total = Counter(
    f"{_METRIC_PREFIX}orders_total", "Total orders", ["type"]
)  # market/limit/stop
deals_total = Counter(f"{_METRIC_PREFIX}deals_total", "Total deals")
positions_open = Gauge(f"{_METRIC_PREFIX}positions_open", "Open positions count")


def classify_error_code(error_code: int | str) -> str:
    """
    Groups MT5 error codes into stable (low cardinality) classes.

    - This mapping can be enriched/adjusted depending on the broker/use.
    """
    try:
        code = int(error_code)
    except (TypeError, ValueError):
        return "unknown"

    # examples of classes (for information / generic)
    if code in {0}:
        return "ok"
    if code in {10004, 10006, 10009}:
        return "network_io"  # timeouts, network
    if code in {4106, 4107, 4110}:
        return "trade_context"  # busy/disabled
    if code in {10030, 10031, 10032}:
        return "server_overload"
    if 130 <= code <= 139:
        return "invalid_stops"  # stoploss/takeprofit invalids
    if 140 <= code <= 149:
        return "price_related"  # price changed/off quotes
    if 4100 <= code <= 4199:
        return "trade_errors"  # large famille MT5 trade errors
    return "other"


# ──────────────────────────────────────────────────────────────────────────────
# Execution Channel (Infra-level health)
# ──────────────────────────────────────────────────────────────────────────────
exec_channel_total = Counter(
    f"{_METRIC_PREFIX}exec_channel_total",
    "Total MT5 execution channel calls by result code",
    ["call", "code", "channel"],
)
exec_channel_latency_ms = Histogram(
    f"{_METRIC_PREFIX}exec_channel_latency_ms",
    "Latency of MT5 API calls in milliseconds",
    buckets=(1, 2, 5, 10, 25, 50, 100, 250, 500, 1000, 2000),
)


# ──────────────────────────────────────────────────────────────────────────────
# Utility API
# ──────────────────────────────────────────────────────────────────────────────
def record_order_reject(error_code: int | str, *, symbol: str | None = None) -> None:
    """
    Increments rejection metrics in a controlled manner:

    - Always: `order_reject_class_total{symbol,error_class}`
    - Optional (opt-in): `order_reject_total{error_code}` with limit
    by allowlist; unauthorized codes are aggregated into "other".
    """
    error_class = classify_error_code(error_code)
    order_reject_class_total.labels(symbol or "UNKNOWN", error_class).inc()

    if _ENABLE_ERROR_CODE_METRIC:
        code_str = str(error_code)
        if _ERROR_CODE_ALLOWLIST:
            label = code_str if code_str in _ERROR_CODE_ALLOWLIST else "other"
        else:
            label = "other"
        order_reject_total.labels(label).inc()
