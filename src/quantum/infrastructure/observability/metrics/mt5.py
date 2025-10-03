from prometheus_client import Counter, Gauge, Histogram

# Latencies
order_check_latency_ms = Histogram(
    "mt5_order_check_latency_ms",
    "Latency of OrderCheck in ms",
    buckets=(10, 25, 50, 100, 200, 400, 800, 1600, 3200),
)
order_send_latency_ms = Histogram(
    "mt5_order_send_latency_ms",
    "Latency of OrderSend in ms",
    buckets=(10, 25, 50, 100, 200, 400, 800, 1600, 3200),
)
time_to_fill_ms = Histogram(
    "mt5_time_to_fill_ms",
    "Time from submit to fill in ms",
    buckets=(10, 25, 50, 100, 200, 400, 800, 1600, 3200, 6400),
)
intent_to_ack_ms = Histogram(
    "mt5_intent_to_ack_ms",
    "Time from intent emission to broker ACK in ms",
    buckets=(10, 25, 50, 100, 200, 400, 800, 1600, 3200),
)

# Execution quality
requotes_total = Counter("mt5_requotes_total", "Total requotes", ["symbol"])
order_reject_total = Counter(
    "mt5_order_reject_total", "Total order rejects", ["symbol", "error_code"]
)
order_reject_class_total = Counter(
    "mt5_order_reject_class_total",
    "Total order rejects by error class",
    ["symbol", "error_class"],
)
partial_fills_total = Counter("mt5_partial_fills_total", "Total partial fills")

slippage_points = Histogram(
    "mt5_slippage_points",
    "Observed slippage in points",
    buckets=(0.1, 0.2, 0.5, 1, 2, 5, 10),
)

# Terminal health
terminal_up = Gauge("mt5_terminal_up", "Terminal health 0/1")
account_free_margin = Gauge("mt5_account_free_margin", "Free margin")
connection_status = Gauge("mt5_connection_status", "Connection: 0=down,1=up,2=degraded")
tick_staleness_ms = Histogram(
    "mt5_tick_staleness_ms",
    "Market data staleness in ms",
    buckets=(100, 250, 500, 1000, 1500, 2000, 3000, 5000),
)

# Flow
intents_total = Counter("mt5_intents_total", "Total trade intents")
orders_total = Counter(
    "mt5_orders_total", "Total orders", ["type"]
)  # market/limit/stop
deals_total = Counter("mt5_deals_total", "Total deals")
positions_open = Gauge("mt5_positions_open", "Open positions count")


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
