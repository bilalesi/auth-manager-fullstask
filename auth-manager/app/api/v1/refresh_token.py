"""Update refresh token endpoint."""

from fastapi import APIRouter, status

from app.core.errors import ErrorKeys
from app.core.exceptions import DatabaseError, KeycloakError
from app.core.guards import guard_auth_error
from app.core.logging import get_logger
from app.core.security import ValidatedTokenDep
from app.dependencies import KeycloakDep, TokenVaultServiceDep
from app.models.api import Ok
from app.models.request import RefreshTokenPayload
from app.models.response import RefreshTokenIdResult, ValidationErrorResponse

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    "/refresh-token",
    response_model=Ok[RefreshTokenIdResult],
    status_code=status.HTTP_200_OK,
    summary="Generate new refresh token id",
    description="Refreshes the user's refresh token and returns a new persistent token id.",
    responses={422: {"model": ValidationErrorResponse}},
)
async def store_refresh_token(
    validated_token: ValidatedTokenDep,
    vault: TokenVaultServiceDep,
    keycloak: KeycloakDep,
    payload: RefreshTokenPayload,
) -> Ok[RefreshTokenIdResult]:
    """
    Stores a refresh token and returns a new persistent token id.

    This endpoint validates the user's current session and stores a new refresh token in the token vault.
    It associates the token with the user's id and session state, ensuring proper authentication tracking.

    Args:
        validated_token: Dependency containing validated token information including user_id and session_state_id
        vault: Dependency providing access to token storage functionality
        payload: Request payload containing the refresh token to store

    Returns:
        Ok[RefreshTokenIdResult]: Success response containing the new persistent token id

    Raises:
        DatabaseError: If storing the refresh token fails
        HTTPException: If token validation fails or other auth errors occur
    """

    user_id = validated_token.user_id
    session_id = validated_token.session_state_id

    with guard_auth_error(
        KeycloakError,
        error_message="Provided Refresh token is not valid",
        error_code=ErrorKeys.validation_error.name,
    ):
        await keycloak.decode_token(token=payload.refresh_token, validate=False)

    with guard_auth_error(
        DatabaseError,
        "Inserting new refresh token failed",
    ):
        new_token_id = await vault.upsert_refresh_token(
            user_id=user_id,
            token=payload.refresh_token,
            session_state_id=session_id,
        )

    return Ok(
        data=RefreshTokenIdResult(
            id=new_token_id,
        )
    )
