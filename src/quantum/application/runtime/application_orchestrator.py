from quantum.application.ports.inbound.application_runtime_port import (
    ApplicationRuntimePort,
)
from quantum.application.runtime.application_component_registry import (
    ApplicationComponentRegistry,
)
from quantum.application.runtime.application_lifecycle_error import (
    ApplicationComponentShutdownError,
    ApplicationComponentStartupError,
    ApplicationLifecycleStateError,
)
from quantum.application.runtime.application_lifecycle_state import (
    ApplicationLifecycleState,
)
from quantum.application.runtime.lifecycle_component import LifecycleComponent


class ApplicationOrchestrator(ApplicationRuntimePort):
    """
    Technical lifecycle coordinator for the Application layer.

    Responsibilities:
    - start registered application components in deterministic order;
    - stop started components in reverse order;
    - expose application lifecycle state;
    - remain free of business orchestration.

    Forbidden:
    - no Decision -> Capital -> Sizing -> Trading workflow;
    - no direct business saga;
    - no domain decision logic;
    - no infrastructure-specific logic.
    """

    __slots__ = (
        "_registry",
        "_state",
        "_started_components",
    )

    def __init__(
        self,
        *,
        registry: ApplicationComponentRegistry,
    ) -> None:
        self._registry = registry
        self._state = ApplicationLifecycleState.NEW
        self._started_components: list[LifecycleComponent] = []

    @property
    def state(self) -> ApplicationLifecycleState:
        return self._state

    async def start(self) -> None:
        if self._state is ApplicationLifecycleState.STARTED:
            return

        if self._state not in (
            ApplicationLifecycleState.NEW,
            ApplicationLifecycleState.STOPPED,
        ):
            raise ApplicationLifecycleStateError(
                f"Cannot start application from state {self._state.name}"
            )

        self._state = ApplicationLifecycleState.STARTING
        self._started_components.clear()

        try:
            for component in self._registry.startup_order():
                await component.start()
                self._started_components.append(component)

        except Exception as exc:
            self._state = ApplicationLifecycleState.FAILED

            await self._rollback_partial_startup()

            raise ApplicationComponentStartupError(
                f"Failed to start application component " f"'{component.name}'"
            ) from exc

        self._state = ApplicationLifecycleState.STARTED

    async def stop(self) -> None:
        if self._state in (
            ApplicationLifecycleState.NEW,
            ApplicationLifecycleState.STOPPED,
        ):
            self._state = ApplicationLifecycleState.STOPPED
            return

        if self._state is ApplicationLifecycleState.STOPPING:
            return

        if self._state not in (
            ApplicationLifecycleState.STARTED,
            ApplicationLifecycleState.FAILED,
        ):
            raise ApplicationLifecycleStateError(
                f"Cannot stop application from state {self._state.name}"
            )

        self._state = ApplicationLifecycleState.STOPPING

        errors: list[BaseException] = []

        for component in reversed(self._started_components):
            try:
                await component.stop()
            except Exception as exc:
                errors.append(exc)

        self._started_components.clear()

        if errors:
            self._state = ApplicationLifecycleState.FAILED
            raise ApplicationComponentShutdownError(
                f"{len(errors)} application component(s) failed during shutdown"
            ) from errors[0]

        self._state = ApplicationLifecycleState.STOPPED

    async def _rollback_partial_startup(self) -> None:
        for component in reversed(self._started_components):
            try:
                await component.stop()
            except Exception:
                # Startup failure rollback must be best-effort.
                # The original startup error remains the primary failure.
                pass

        self._started_components.clear()
