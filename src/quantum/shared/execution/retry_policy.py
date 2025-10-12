from quantum.shared.types.execution import ExecutionCode


def should_retry(code: ExecutionCode) -> bool:
    """
    Determines whether an operation should be retried based on its execution code.

    This function is shared between application and infrastructure layers.
    It encapsulates retry semantics (idempotent, transient-safe operations).
    """
    return code in {
        ExecutionCode.INTERNAL_FAIL,
        ExecutionCode.INTERNAL_FAIL_TIMEOUT,
        ExecutionCode.INTERNAL_FAIL_CONNECT,
    }
