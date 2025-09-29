from pydantic import BaseModel


class LogPayloadV1(BaseModel):
    model_config = {
        "extra": "allow",
        "frozen": True,
    }  # Accept any additional dynamic keys (extra fields)
    timestamp: str
    ts_unix_ms: int | None = None
    ts_monotonic_ms: int | None = None
    level: str
    logger: str
    message: str
    env: str
    instance: str
    trace_id: str | None
    span_id: str | None
    sampled: bool | None
    correlation_id: str | None
    run_id: str | None
    exception: str | None = None
    log_schema_version: str = "v1"
    validation_error: str | None = None

    def to_clean_json(self) -> str:
        return self.model_dump_json(exclude_none=True, by_alias=True)
