from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError
from starlette.responses import Response

from app.core.errors import ErrorKeys, errors_mapping
from app.core.exceptions import AuthManagerError
from app.core.logging import get_logger
from app.models.api import Err

logger = get_logger(__name__)


async def auth_manager_error_handler(
    _: Request,
    exc: AuthManagerError,
) -> Response:
    """Handle custom AuthManagerError exceptions."""

    status_code = errors_mapping.get(exc.code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    error_response = Err(
        error=exc.message,
        code=exc.code,
        details=exc.details,
        reason=None,
    )
    logger.error("auth_manager_error_handler", error=error_response.model_dump_json())

    return Response(
        content=error_response.model_dump_json(),
        status_code=status_code,
        media_type="application/json",
    )


async def request_validation_error_handler(
    _: Request,
    exc: RequestValidationError,
) -> Response:
    """Handle FastAPI request validation errors."""

    formatted_errors = {".".join(map(str, err["loc"])): err["msg"] for err in exc.errors()}
    error_response = Err(
        error="Validation error",
        code=ErrorKeys.validation_error.name,
        reason="Request parameters validation failed",
        details=formatted_errors,
    )
    logger.error("request_validation_error_handler", error=error_response.model_dump_json())

    return Response(
        content=error_response.model_dump_json(),
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        media_type="application/json",
    )


async def pydantic_validation_error_handler(
    _: Request,
    exc: PydanticValidationError,
) -> Response:
    """Handle Pydantic validation errors."""

    field_errors = {}
    for err in exc.errors():
        field_name = err["loc"][-1] if err.get("loc") else "unknown_field"
        field_errors[field_name] = err["msg"]

    error_response = Err(
        error="Validation error",
        code=ErrorKeys.validation_error.name,
        reason=f"{len(field_errors)} field(s) failed validation",
        details=field_errors,
    )
    logger.error("pydantic_validation_error_handler", error=error_response.model_dump_json())

    return Response(
        content=error_response.model_dump_json(),
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        media_type="application/json",
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> Response:
    """Handle all other unhandled exceptions."""

    error_response = Err(
        error="Internal server error",
        code=ErrorKeys.internal_error.name,
        reason=str(exc),
    )
    logger.exception(
        "unhandled_exception",
        error_type=type(exc).__name__,
        path=str(request.url.path),
        error=error_response.model_dump_json(),
    )

    return Response(
        content=error_response.model_dump_json(),
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        media_type="application/json",
    )
