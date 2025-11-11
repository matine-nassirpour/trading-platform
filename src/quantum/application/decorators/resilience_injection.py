from __future__ import annotations

import inspect

from collections.abc import Callable
from functools import wraps
from typing import Any, Protocol, TypeVar, cast, overload

from quantum.application.policies.resilience_policy import (
    ResilienceConfig,
    resilient_async_call,
    resilient_call,
)
from quantum.application.policies.retry_policy import RetryPolicy
from quantum.application.ports.outbound.timeout_runner_port import TimeoutRunnerPort

C = TypeVar("C", bound=object)


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Protocol: ResilientCallable                                                │
# ╰────────────────────────────────────────────────────────────────────────────╯
class ResilientCallable(Protocol):
    _resilience_call_name: str
    _resilience_bound: bool
    _resilience_operation: str

    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Internal Helper                                                            │
# ╰────────────────────────────────────────────────────────────────────────────╯
def _apply_resilient(
    fn: Callable[..., Any],
    *,
    is_async: bool,
    runner: TimeoutRunnerPort,
    policy: RetryPolicy | None,
    cfg: ResilienceConfig | None,
) -> ResilientCallable:
    """Internal helper to apply the correct resilient decorator to a function."""
    decorator: Callable[..., Any]

    if is_async:
        decorator = resilient_async_call(timeout_runner=runner, policy=policy, cfg=cfg)
    else:
        decorator = resilient_call(timeout_runner=runner, policy=policy, cfg=cfg)

    return cast(ResilientCallable, decorator(fn))


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Public Decorator                                                           │
# ╰────────────────────────────────────────────────────────────────────────────╯
@overload
def bind_resilience(cls: type[C]) -> type[C]: ...
@overload
def bind_resilience(
    *,
    timeout_runner: TimeoutRunnerPort | None = None,
    policy: RetryPolicy | None = None,
    cfg: ResilienceConfig | None = None,
) -> Callable[[type[C]], type[C]]: ...


def bind_resilience(
    cls: type[C] | None = None,
    *,
    timeout_runner: TimeoutRunnerPort | None = None,
    policy: RetryPolicy | None = None,
    cfg: ResilienceConfig | None = None,
) -> type[C] | Callable[[type[C]], type[C]]:
    """
    Class decorator that dynamically binds @resilient_call and @resilient_async_call
    with the appropriate timeout_runner, retry policy and configuration.

    Can be used either as:
        @bind_resilience
        class MyService: ...

    or with parameters:
        @bind_resilience(timeout_runner=my_runner)
        class MyService: ...
    """

    def class_decorator(inner_cls: type[C]) -> type[C]:
        original_init = cast(Callable[..., None], inner_cls.__init__)

        @wraps(original_init)
        def __init__(self: C, *args: Any, **kwargs: Any) -> None:
            # Construct instance normally
            original_init(self, *args, **kwargs)

            # Resolve dependencies
            runner = timeout_runner or getattr(self, "timeout_runner", None)
            retry_policy = policy or getattr(self, "policy", None)
            config = cfg or getattr(self, "cfg", None)

            if runner is None:
                raise RuntimeError(
                    f"[{inner_cls.__name__}] bind_resilience used without timeout_runner injection"
                )

            # Bind all resilient methods dynamically
            for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
                if not hasattr(method, "_resilience_call_name"):
                    continue
                if getattr(method, "_resilience_bound", False):
                    continue

                op_name = method._resilience_call_name
                decorated = _apply_resilient(
                    fn=method,
                    is_async=inspect.iscoroutinefunction(method),
                    runner=runner,
                    policy=retry_policy,
                    cfg=config,
                )

                decorated._resilience_bound = True
                decorated._resilience_operation = op_name
                setattr(self, name, decorated)

        inner_cls.__init__ = __init__  # type: ignore[method-assign, assignment]
        return inner_cls

    if cls is not None:
        # Used as @bind_resilience (without parentheses)
        return class_decorator(cls)

    # Used as @bind_resilience(...)
    return class_decorator
