import os

AUDIT_EVENT_WHITELIST_V1 = {
    "order_submit_v1",
    "order_ack_v1",
    "order_fill_v1",
    "order_reject_v1",
    "killswitch_trigger_v1",
    "reconciliation_v1",
}


def get_audit_whitelist(version: str | None = None) -> set[str]:
    """
    Returns the whitelist by version, extended by QUANTUM_AUDIT_EVENTS (csv).
    """
    baseline = (
        AUDIT_EVENT_WHITELIST_V1 if (version is None or version == "v1") else set()
    )
    extra_csv = os.getenv("QUANTUM_AUDIT_EVENTS", "").strip()
    extras = {x.strip() for x in extra_csv.split(",")} if extra_csv else set()
    return set(baseline) | {e for e in extras if e}
