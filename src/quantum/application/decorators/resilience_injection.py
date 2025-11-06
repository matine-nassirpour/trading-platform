from __future__ import annotations

import inspect

from collections.abc import Callable
from functools import wraps
from typing import TypeVar, cast

from quantum.application.policies.resilience_policy import (
    ResilienceConfig,
    resilient_async_call,
    resilient_call,
)
from quantum.application.policies.retry_policy import RetryPolicy
from quantum.application.ports.outbound.timeout_runner_port import TimeoutRunnerPort

C = TypeVar("C", bound=object)


def bind_resilience(
    *,
    timeout_runner: TimeoutRunnerPort | None = None,
    policy: RetryPolicy | None = None,
    cfg: ResilienceConfig | None = None,
) -> Callable[[type[C]], type[C]]:
    """
    Class decorator that dynamically binds @resilient_call decorators
    with the appropriate timeout_runner and policy after instantiation.
    """

    def class_decorator(cls: type[C]) -> type[C]:
        original_init = cast(Callable[..., None], cls.__init__)

        @wraps(original_init)
        def __init__(self, *args, **kwargs):
            # Call original constructor first
            original_init(self, *args, **kwargs)

            # Resolve effective dependencies
            runner = timeout_runner or getattr(self, "timeout_runner", None)
            retry_policy = policy or getattr(self, "policy", None)
            config = cfg or getattr(self, "cfg", None)

            if runner is None:
                raise RuntimeError(
                    f"[{cls.__name__}] bind_resilience used without timeout_runner injection"
                )

            # Iterate through instance methods
            for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
                # Skip non-resilient methods
                if not hasattr(method, "_resilience_call_name"):
                    continue

                # Skip already bound (idempotence guarantee)
                if getattr(method, "_resilience_bound", False):
                    continue

                op_name = method._resilience_call_name

                # Detect async vs sync wrapper automatically
                if inspect.iscoroutinefunction(method):
                    decorated = resilient_async_call(
                        timeout_runner=runner, policy=retry_policy, cfg=config
                    )(method)
                else:
                    decorated = resilient_call(
                        timeout_runner=runner, policy=retry_policy, cfg=config
                    )(method)

                # Mark as bound to avoid future rewrapping
                decorated._resilience_bound = True
                decorated._resilience_operation = op_name

                # Replace method on instance
                setattr(self, name, decorated)

        cls.__init__ = __init__
        return cls

    return class_decorator
