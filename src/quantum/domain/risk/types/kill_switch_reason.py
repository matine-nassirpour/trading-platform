from enum import StrEnum


class KillSwitchReason(StrEnum):
    RISK_LIMIT = "risk_limit"
    NETWORK = "network"
    BROKER_REJECTS = "broker_rejects"
    MANUAL = "manual"
