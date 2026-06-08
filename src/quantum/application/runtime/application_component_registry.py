from dataclasses import dataclass, field

from quantum.application.runtime.lifecycle_component import LifecycleComponent
from quantum.application.shared.errors.application_error import (
    ApplicationInvariantViolationError,
)


@dataclass(slots=True)
class ApplicationComponentRegistry:
    """
    Ordered registry of application lifecycle components.

    Startup order:
    - insertion order

    Shutdown order:
    - reverse insertion order
    """

    _components: list[LifecycleComponent] = field(default_factory=list)
    _names: set[str] = field(default_factory=set)

    def register(self, component: LifecycleComponent) -> None:
        if not component.name.strip():
            raise ApplicationInvariantViolationError(
                "Lifecycle component name must not be blank"
            )

        if component.name in self._names:
            raise ApplicationInvariantViolationError(
                f"Lifecycle component already registered: {component.name}"
            )

        self._components.append(component)
        self._names.add(component.name)

    def startup_order(self) -> tuple[LifecycleComponent, ...]:
        return tuple(self._components)

    def shutdown_order(self) -> tuple[LifecycleComponent, ...]:
        return tuple(reversed(self._components))
