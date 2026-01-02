from __future__ import annotations

import inspect
import logging

from collections.abc import Callable
from functools import wraps
from typing import Any, Final, Protocol, TypeVar, cast, overload

from quantum.infrastructure.execution.ports.timeout_runner_port import TimeoutRunnerPort
from quantum.infrastructure.execution.resilience import (
    ResilienceConfig,
    RetryPolicy,
    resilient_async_call,
    resilient_call,
)

LOGGER: Final = logging.getLogger(__name__)
C = TypeVar("C", bound=object)


class ResilienceBindingError(Exception):
    """Raised when the @bind_resilience decorator cannot inject required components."""

    def __init__(self, cls_name: str, missing: str) -> None:
        msg = f"[{cls_name}] resilience binding failed — missing dependency: {missing}"
        super().__init__(msg)
        self.cls_name = cls_name
        self.missing = missing


class ResilientCallable(Protocol):
    """Marker protocol for methods decorated with resilient_call wrappers."""

    _resilience_call_name: str
    _resilience_bound: bool
    _resilience_operation: str

    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...


def _apply_resilient(
    fn: Callable[..., Any],
    *,
    is_async: bool,
    runner: TimeoutRunnerPort,
    policy: RetryPolicy | None,
    cfg: ResilienceConfig | None,
) -> ResilientCallable:
    """
    Internal helper to apply the appropriate resilient decorator
    (sync or async) to a method dynamically.
    """
    decorator: Callable[..., Any]
    if is_async:
        decorator = resilient_async_call(timeout_runner=runner, policy=policy, cfg=cfg)
    else:
        decorator = resilient_call(timeout_runner=runner, policy=policy, cfg=cfg)
    return cast(ResilientCallable, decorator(fn))


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
    Class decorator that dynamically binds all resilient_* decorators
    (sync and async) with the injected timeout_runner, retry policy, and config.

    Usage:
        @bind_resilience
        class MyService: ...

        @bind_resilience(timeout_runner=my_runner, policy=my_policy)
        class MyService: ...

    It searches for methods marked with `_resilience_call_name`
    and rebinds them with the proper runtime parameters.
    """

    def class_decorator(inner_cls: type[C]) -> type[C]:
        original_init = cast(Callable[..., None], inner_cls.__init__)

        @wraps(original_init)
        def __init__(self: C, *args: Any, **kwargs: Any) -> None:
            # Construct instance normally
            original_init(self, *args, **kwargs)

            # Resolve injected dependencies
            runner = timeout_runner or getattr(self, "timeout_runner", None)
            retry_policy = policy or getattr(self, "policy", None)
            config = cfg or getattr(self, "cfg", None)

            if runner is None:
                raise ResilienceBindingError(inner_cls.__name__, "timeout_runner")

            # Dynamically rebind resilient methods
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
                LOGGER.debug(
                    "[ResilienceInjection] Bound %s.%s → operation=%s",
                    inner_cls.__name__,
                    name,
                    op_name,
                )

        inner_cls.__init__ = __init__  # type: ignore[method-assign, assignment]
        return inner_cls

    # Allow both @bind_resilience and @bind_resilience(...)
    return class_decorator(cls) if cls is not None else class_decorator
