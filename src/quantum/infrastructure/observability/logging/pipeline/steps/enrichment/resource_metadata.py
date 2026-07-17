import logging

from quantum.infrastructure.observability.foundation.config.identity_runtime_bundle import (
    IdentityRuntimeBundle,
)
from quantum.infrastructure.observability.logging.pipeline.engine.step import (
    PipelineStep,
)


class ResourceMetadataStep(PipelineStep):
    """
    Injects resource metadata: env, namespace, service_name, version.
    """

    def __init__(self, identity: IdentityRuntimeBundle):
        self.identity = identity

    def process(self, record: logging.LogRecord) -> bool:
        record.env = getattr(record, "env", self.identity.environment)
        record.service_namespace = getattr(
            record, "service_namespace", self.identity.service_namespace
        )
        record.service_name = getattr(
            record, "service_name", self.identity.service_name
        )
        record.service_version = getattr(
            record, "service_version", self.identity.service_version
        )
        record.instance_id = getattr(record, "instance_id", self.identity.instance_id)
        return True
