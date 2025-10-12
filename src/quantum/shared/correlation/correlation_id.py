import contextvars
import uuid
from contextlib import contextmanager

# ContextVar globally accessible (thread-safe, async-safe)
correlation_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "quantum.correlation_id", default=None
)


def get_correlation_id() -> str | None:
    return correlation_id_ctx.get()


def set_correlation_id(value: str | None) -> None:
    if value is not None:
        try:
            uuid.UUID(value)
        except Exception:
            raise ValueError("correlation_id must be a valid UUID")
    correlation_id_ctx.set(value)


def new_correlation_id() -> str:
    cid = str(uuid.uuid4())
    correlation_id_ctx.set(cid)
    return cid


@contextmanager
def correlation_context(correlation_id: str | None = None):
    """
    Context manager to execute a block with a given (or new) correlation_id.
    """
    token = correlation_id_ctx.set(correlation_id or str(uuid.uuid4()))
    try:
        yield
    finally:
        correlation_id_ctx.reset(token)
