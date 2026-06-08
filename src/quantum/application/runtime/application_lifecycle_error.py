from quantum.application.shared.errors.application_error import ApplicationError


class ApplicationLifecycleError(ApplicationError):
    """Raised when application lifecycle coordination fails."""


class ApplicationLifecycleStateError(ApplicationLifecycleError):
    """Raised when lifecycle state transition is invalid."""


class ApplicationComponentStartupError(ApplicationLifecycleError):
    """Raised when an application component fails during startup."""


class ApplicationComponentShutdownError(ApplicationLifecycleError):
    """Raised when an application component fails during shutdown."""
