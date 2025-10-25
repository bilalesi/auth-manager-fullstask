"""Guard context managers for common validation patterns."""

from contextlib import contextmanager
from typing import Callable, Iterator, Type, TypeVar

from sqlalchemy.exc import NoResultFound

from app.core.errors import ErrorKeys
from app.core.exceptions import AuthManagerError

T = TypeVar("T")


@contextmanager
def guard_raise_if_not_found(
    exc: Exception,
) -> Iterator[None]:
    """Guard that raises error when database query returns no results.

    Args:
        error_message: Error message to raise
        error_code: Error code for the exception

    Yields:
        None

    Raises:
        Exception: If NoResultFound is raised

    """
    try:
        yield
    except NoResultFound as err:
        raise exc from err


@contextmanager
def guard_invariant(
    value: T,
    condition: Callable[[T], bool],
    exc: Exception,
) -> Iterator[T]:
    """
    Invariant guard

    Ensures `condition(value)` is False. If True, raises `exc`.

    Args:
        value: Any object to guard
        condition: Callable that returns True if invariant is violated
        exc: Exception to raise on violation

    Yields:
        The original `value`

    Example:
        with guard_invariant(entry, lambda e: e.token is None, ValidationError(...)) as e:
            reveal_type(e.token)  # str, not Optional[str]
    """
    if condition(value):
        raise exc
    # TODO: find the solution to narrow down the value type
    # as checked None value
    yield value


@contextmanager
def guard_auth_error(
    exc: Type[AuthManagerError] | None,
    error_message: str,
    error_code: str | None = None,
) -> Iterator[None]:
    """
    Wrap a block and re-raise any exception as the specified exception type.

    Args:
        exc: AuthManagerError

    Yields:
        None

    Raises:
        Exception
    """
    try:
        yield
    except AuthManagerError as ex:
        if exc:
            raise exc(error_message)
        raise AuthManagerError(
            message=ex.message or error_message,
            code=ex.code,
            details=ex.details,
        ) from ex
    except Exception as ex:
        raise AuthManagerError(
            message=str(ex) or error_message,
            code=error_code or ErrorKeys.internal_error.name,
        ) from ex
