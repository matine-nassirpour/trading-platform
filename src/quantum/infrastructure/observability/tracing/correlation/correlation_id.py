import contextvars
import uuid

from collections.abc import Generator
from contextlib import contextmanager

# ╭────────────────────────────────────────────────────────────────────────────╮
# │ ContextVar (thread-safe & async-safe)                                      │
# ╰────────────────────────────────────────────────────────────────────────────╯
correlation_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "quantum.correlation_id", default=None
)


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Core API                                                                   │
# ╰────────────────────────────────────────────────────────────────────────────╯
def get_correlation_id() -> str | None:
    """
    Retrieve the current correlation ID from the active context.
    """
    return correlation_id_ctx.get()


def set_correlation_id(value: str | None) -> None:
    """
    Set the correlation ID for the current context.
    """
    if value is not None:
        try:
            uuid.UUID(value)
        except Exception:
            raise ValueError(f"Invalid correlation_id: {value!r}") from None
    correlation_id_ctx.set(value)


def generate_correlation_id() -> str:
    """
    Generate and set a new correlation ID for the current context.
    """
    cid = str(uuid.uuid4())
    correlation_id_ctx.set(cid)
    return cid


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Context Manager                                                            │
# ╰────────────────────────────────────────────────────────────────────────────╯
@contextmanager
def correlation_context(
    correlation_id: str | None = None,
) -> Generator[None, None, None]:
    """
    Context manager to execute a block under a specific correlation ID.
    """
    cid = correlation_id or str(uuid.uuid4())
    try:
        uuid.UUID(cid)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid correlation_id: {cid!r}") from None

    token = correlation_id_ctx.set(cid)
    try:
        yield
    finally:
        correlation_id_ctx.reset(token)
