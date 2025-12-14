"""Result types for explicit error handling (functional programming pattern)."""
from typing import TypedDict, Union, Literal, Generic, TypeVar

T = TypeVar('T')


class Success(TypedDict, Generic[T]):
    """Successful operation result."""
    status: Literal['success']
    data: T


class Failure(TypedDict):
    """Failed operation result."""
    status: Literal['error']
    error: str


Result = Union[Success[T], Failure]


def success(data: T) -> Success[T]:
    """Create a successful result.

    Args:
        data: The successful result data

    Returns:
        Success result containing the data

    Example:
        >>> result = success([{"PAGE_NO": 1, "ROTATION": 0}])
        >>> if result['status'] == 'success':
        ...     print(result['data'])
    """
    return {'status': 'success', 'data': data}


def failure(error: str) -> Failure:
    """Create a failure result.

    Args:
        error: Error message describing what went wrong

    Returns:
        Failure result containing the error

    Example:
        >>> result = failure("API timeout after 30 seconds")
        >>> if result['status'] == 'error':
        ...     print(result['error'])
    """
    return {'status': 'error', 'error': error}


def is_success(result: Result[T]) -> bool:
    """Check if result is successful.

    Args:
        result: Result to check

    Returns:
        True if result is successful, False otherwise
    """
    return result['status'] == 'success'


def is_failure(result: Result[T]) -> bool:
    """Check if result is a failure.

    Args:
        result: Result to check

    Returns:
        True if result is a failure, False otherwise
    """
    return result['status'] == 'error'


def unwrap(result: Result[T]) -> T:
    """Extract data from successful result or raise exception.

    Args:
        result: Result to unwrap

    Returns:
        The data if result is successful

    Raises:
        ValueError: If result is a failure

    Example:
        >>> result = success([1, 2, 3])
        >>> data = unwrap(result)  # Returns [1, 2, 3]

        >>> result = failure("Not found")
        >>> data = unwrap(result)  # Raises ValueError
    """
    if is_success(result):
        return result['data']
    raise ValueError(f"Attempted to unwrap failed result: {result['error']}")


def unwrap_or(result: Result[T], default: T) -> T:
    """Extract data from result or return default value.

    Args:
        result: Result to unwrap
        default: Default value to return if result is failure

    Returns:
        The data if successful, otherwise the default value

    Example:
        >>> result = failure("Not found")
        >>> data = unwrap_or(result, [])  # Returns []
    """
    if is_success(result):
        return result['data']
    return default
