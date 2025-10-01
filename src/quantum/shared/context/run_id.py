import contextvars
import uuid

# Context thread-safe / async-safe
_run_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "quantum.run_id", default=None
)


def generate_run_id() -> str:
    run_id = str(uuid.uuid4())
    _run_id_ctx.set(run_id)
    return run_id


def get_run_id() -> str | None:
    return _run_id_ctx.get()
