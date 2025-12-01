from dataclasses import dataclass


@dataclass(frozen=True)
class CoreConfig:
    environment: str
    service_namespace: str
    service_name: str
    service_version: str
    instance_id: str
