import contextvars
import uuid
from contextlib import contextmanager

# Context thread-safe / async-safe
_run_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "quantum.run_id", default=None
)


def is_valid_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except (ValueError, TypeError):
        return False


def set_run_id(value: str) -> None:
    if not is_valid_uuid(value):
        raise ValueError("run_id must be a valid UUID string")
    _run_id_ctx.set(value)


@contextmanager
def run_id_context(run_id: str | None = None):
    token = _run_id_ctx.set(run_id or str(uuid.uuid4()))
    try:
        yield
    finally:
        _run_id_ctx.reset(token)


def generate_run_id() -> str:
    run_id = str(uuid.uuid4())
    _run_id_ctx.set(run_id)
    return run_id


def get_run_id() -> str | None:
    return _run_id_ctx.get()
