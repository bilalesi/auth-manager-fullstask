"""Offline token generation and revocation endpoints."""

import asyncio
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.core.exceptions import DatabaseError, KeycloakError, TokenNotFoundError
from app.core.guards import guard_auth_error, guard_invariant
from app.core.logging import get_logger
from app.core.security import ValidatedTokenDep
from app.db.models import TokenType
from app.dependencies import KeycloakDep, TokenVaultServiceDep
from app.models.api import Ok
from app.models.response import (
    OfflineTokenResult,
    OfflineTokenRevocationResponse,
    ValidationErrorResponse,
)

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    "/offline-token-id",
    response_model=Ok[OfflineTokenResult],
    status_code=status.HTTP_200_OK,
    summary="Generate new offline token",
    description="Generates a new offline token from an existing offline token without requiring user consent.",
)
async def make_offline_token(
    validated_token: ValidatedTokenDep,
    keycloak: KeycloakDep,
    vault: TokenVaultServiceDep,
) -> Ok[OfflineTokenResult]:
    """Generate a new offline token from an existing offline token.

    This endpoint allows generating additional offline tokens without requiring
    user consent again. It retrieves an existing offline token from the vault
    by session_state_id, uses it to request a new offline token from Keycloak,
    encrypts and stores the new offline token, and returns the persistent token ID.

    Args:
        validated_token: Validated token with user information (validated by dependency)
        keycloak: Keycloak service dependency
        vault: Token vault service dependency

    Returns:
        OkResponse containing OfflineTokenResponse with new persistent_token_id

    Raises:
        UnauthorizedError: If bearer token is missing or invalid
        TokenNotFoundError: If no offline token found for the session (404)
        KeycloakError: If offline token request fails
    """

    user_id = validated_token.user_id
    session_state_id = validated_token.session_state_id

    with guard_auth_error(
        None,
        "No offline token was found to generate a new one",
    ):
        entry, decrypted_token = await vault.retrieve_by_session_state_id_or_panic(
            session_state_id=session_state_id,
            token_type=TokenType.OFFLINE,
        )

    with guard_auth_error(
        None,
        "Keycloak generating new offline token failed",
    ):
        # basically it return the same offline token already stored for the session
        new_token_response = await keycloak.request_offline_token(decrypted_token)

    with guard_invariant(
        new_token_response,
        lambda e: e.refresh_token is None,
        KeycloakError(
            "Could not generate new token",
        ),
    ):
        new_entry = await vault.store(
            user_id=user_id,
            token=new_token_response.refresh_token,
            token_type=TokenType.OFFLINE,
            session_state_id=new_token_response.session_state,
            attributes={
                "from": str(entry.id),
            },
        )

        return Ok(
            data=OfflineTokenResult(
                persistent_token_id=new_entry.id,
                session_state_id=new_entry.session_state_id,
            )
        )


@router.delete(
    "/offline-token-id",
    response_model=Ok[OfflineTokenRevocationResponse],
    status_code=status.HTTP_200_OK,
    summary="Revoke offline token",
    description="Revokes an offline token, deletes it from the vault, and optionally revokes the Keycloak session if no other tokens share it.",
    responses={422: {"model": ValidationErrorResponse}},
)
async def revoke_offline_token(
    keycloak: KeycloakDep,
    vault: TokenVaultServiceDep,
    _: ValidatedTokenDep,
    id: UUID = Query(..., description="Persistent token ID (uuid) to revoke"),
) -> Ok[OfflineTokenRevocationResponse]:
    """Revoke an offline token and delete it from the vault.

    Args:
        validated_token: Validated token with user information (validated by dependency)
        id: Persistent token id (uuid) to revoke
        keycloak: Keycloak service dependency
        token_vault: Token vault service dependency

    Returns:
        OkResponse containing OfflineTokenRevocationResponse with revocation details

    Raises:
        UnauthorizedError: If bearer token is missing or invalid
        TokenNotFoundError: If token not found
        KeycloakError: If token or session revocation fails
    """

    with guard_auth_error(
        TokenNotFoundError,
        "No offline token was found",
    ):
        entry, _ = await vault.retrieve_and_decrypt(id)

    with guard_auth_error(
        DatabaseError,
        "Delete operation failed",
    ):
        deleted = await vault.delete_token(entry.id)

    session_revoked = False
    with guard_auth_error(
        KeycloakError,
        f"Revoke session {entry.session_state_id} for token {entry.id} failed",
    ):
        had_shared_session, sessions = await asyncio.gather(
            vault.is_token_shared(
                session_state_id=entry.session_state_id,
                exclude_id=entry.id,
                token_type=TokenType.OFFLINE,
            ),
            keycloak.retrieve_user_sessions(user_id=entry.user_id),
        )

        # NOTE: not sure if checking if active session is still there make sense
        # if the user session id dead, the user can not even make this request
        # check with the JDC/team
        if not had_shared_session and not any(
            session.id == entry.session_state_id for session in sessions
        ):
            await keycloak.revoke_session(entry.session_state_id)
            session_revoked = True

    return Ok(
        data=OfflineTokenRevocationResponse(
            message="Offline token revoked successfully",
            persistent_token_id=entry.id,
            token_deleted=deleted,
            session_revoked=session_revoked,
            had_shared_session=had_shared_session,
        )
    )
