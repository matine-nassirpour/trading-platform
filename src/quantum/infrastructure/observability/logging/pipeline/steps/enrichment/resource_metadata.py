from __future__ import annotations

import logging

from quantum.infrastructure.observability.logging.pipeline.engine.step import (
    PipelineStep,
)


class ResourceMetadataStep(PipelineStep):
    """
    Injects resource metadata: env, namespace, service_name, version.
    """

    def __init__(self, *, env: str, namespace: str, name: str, version: str) -> None:
        self.env = env
        self.namespace = namespace
        self.name = name
        self.version = version

    def process(self, record: logging.LogRecord) -> bool:
        record.env = getattr(record, "env", self.env)
        record.service_name = getattr(record, "service_name", self.name)
        record.service_version = getattr(record, "service_version", self.version)
        record.service_namespace = getattr(record, "service_namespace", self.namespace)
        return True
