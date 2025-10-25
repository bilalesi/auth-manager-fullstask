"""Refresh token ID endpoint."""

from fastapi import APIRouter, status

from app.core.errors import ErrorKeys
from app.core.exceptions import KeycloakError, TokenNotFoundError
from app.core.guards import guard_auth_error, guard_invariant
from app.core.logging import get_logger
from app.core.security import ValidatedTokenDep
from app.db.models import TokenType
from app.dependencies import KeycloakDep, TokenVaultServiceDep
from app.models.api import Ok
from app.models.response import RefreshTokenIdResult, ValidationErrorResponse

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    "/refresh-token-id",
    response_model=Ok[RefreshTokenIdResult],
    status_code=status.HTTP_200_OK,
    summary="Generate new refresh token id",
    description="Refreshes the user's refresh token and returns a new persistent token id.",
    responses={422: {"model": ValidationErrorResponse}},
)
async def make_new_refresh_token_id(
    validated_token: ValidatedTokenDep,
    keycloak: KeycloakDep,
    vault: TokenVaultServiceDep,
) -> Ok[RefreshTokenIdResult]:
    """Generate a new refresh token id.

    This endpoint retrieves the user's existing refresh token, uses it to
    refresh the access token with Keycloak, and stores the new refresh token
    with an upsert operation (ensuring only one refresh token per user).

    Args:
        validated_token: Validated token with user information
        keycloak: Keycloak service dependency
        vault: Token vault service dependency

    Returns:
        OkResponse containing RefreshTokenIdResponse with persistent_token_id

    Raises:
        UnauthorizedError: If bearer token is missing or invalid
        TokenNotFoundError: If no token found
        TokenNotFoundError: If no active refresh token found
        KeycloakError: If refresh token generation fails
    """

    user_id = validated_token.user_id
    session_id = validated_token.session_state_id

    with guard_auth_error(
        None,
        "No refresh token was found with this session",
    ):
        entry, decrypted_token = await vault.retrieve_by_session_state_id_or_panic(
            session_state_id=session_id,
            token_type=TokenType.REFRESH,
        )

    with guard_invariant(
        entry,
        lambda e: not e.encrypted_token or not e.iv,
        TokenNotFoundError(
            "No encrypted refresh token was found",
            ErrorKeys.token_not_found.name,
        ),
    ):
        new_token_response = await keycloak.refresh_access_token(decrypted_token)

    with guard_invariant(
        new_token_response,
        lambda e: e.refresh_token is None,
        KeycloakError("No refresh token was generated"),
    ):
        new_token_id = await vault.upsert_refresh_token(
            user_id=user_id,
            token=new_token_response.refresh_token,
            session_state_id=new_token_response.session_state,
            attributes=None,
        )

        return Ok(
            data=RefreshTokenIdResult(
                id=new_token_id,
            )
        )
