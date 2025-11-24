from typing import Final

from prometheus_client import Counter, Gauge, Histogram

# ╭────────────────────────────────────────────────────────────────────────────╮
# │ MT5 Metrics                                                                │
# ╰────────────────────────────────────────────────────────────────────────────╯
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


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Execution Channel (Infra-level health)                                     │
# ╰────────────────────────────────────────────────────────────────────────────╯
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
