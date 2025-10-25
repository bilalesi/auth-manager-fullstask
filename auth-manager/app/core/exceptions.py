"""Custom exception classes."""

from typing import Any

from app.core.errors import ErrorKeys


class AuthManagerError(Exception):
    """Base exception for Auth Manager."""

    def __init__(self, message: str, code: str = "error", details: dict[str, Any] | None = None):
        self.message = message
        self.code = code
        self.details = details
        super().__init__(message)


class KeycloakError(AuthManagerError):
    """Exception for Keycloak-related errors."""

    def __init__(
        self,
        message: str,
        code: str = ErrorKeys.keycloak_error.name,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, code, details)


class InvalidAckStateError(AuthManagerError):
    """Exception for invalid state token errors."""

    def __init__(
        self,
        message: str,
        code: str = ErrorKeys.invalid_ack_state.name,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, code, details)


class TokenNotFoundError(AuthManagerError):
    """Exception for token not found errors."""

    def __init__(
        self,
        message: str,
        code: str = ErrorKeys.token_not_found.name,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, code, details)


class UnauthorizedError(AuthManagerError):
    """Exception for unauthorized access errors."""

    def __init__(
        self,
        message: str,
        code: str = ErrorKeys.unauthorized.name,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, code, details)


class TokenNotActiveError(AuthManagerError):
    """Exception for inactive token errors."""

    def __init__(
        self,
        message: str,
        code: str = ErrorKeys.token_not_active.name,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, code, details)


class ValidationError(AuthManagerError):
    """Exception for validation errors."""

    def __init__(
        self,
        message: str,
        code: str = ErrorKeys.validation_error.name,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, code, details)


class InvalidRequestError(AuthManagerError):
    """Exception for invalid request errors."""

    def __init__(
        self,
        message: str,
        code: str = ErrorKeys.invalid_request.name,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, code, details)


class DatabaseError(AuthManagerError):
    """Exception for database operation errors."""

    def __init__(
        self,
        message: str,
        code: str = ErrorKeys.database_error.name,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, code, details)
