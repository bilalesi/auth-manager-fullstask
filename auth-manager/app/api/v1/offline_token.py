"""Offline token consent and callback endpoints."""

import secrets
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Query, status
from keycloak import urls_patterns
from starlette.responses import RedirectResponse

from app.config import get_settings
from app.core.exceptions import AuthManagerError
from app.core.logging import get_logger
from app.core.security import ValidatedTokenDep
from app.db.models import TokenType
from app.dependencies import AckStateDep, KeycloakDep, TokenVaultServiceDep
from app.models.api import Ok
from app.models.response import OfflineConsentResult, OfflineTokenResult, ValidationErrorResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/offline-token")
config = get_settings()


@router.get(
    "/callback",
    response_model=Ok[OfflineTokenResult],
    status_code=status.HTTP_200_OK,
    summary="Offline token OAuth callback",
    description="Handles the OAuth callback after user consent, exchanges authorization code for tokens, and stores the offline token.",
    responses={422: {"model": ValidationErrorResponse}},
)
async def offline_token_callback(
    keycloak: KeycloakDep,
    ack_state_service: AckStateDep,
    vault_service: TokenVaultServiceDep,
    code: str = Query(..., description="Authorization code from Keycloak"),
    state: str = Query(..., description="Ack state token for validation"),
    error: Optional[str] = Query(None, description="Error code from Keycloak"),
    error_description: Optional[str] = Query(None, description="Error description from Keycloak"),
) -> RedirectResponse:
    """Handle OAuth callback after user consent for offline access.

    This endpoint receives the OAuth callback from Keycloak after the user
    grants consent for offline access. It validates the state token, exchanges
    the authorization code for tokens, encrypts and stores the offline token,
    and returns the persistent token id.


    Args:
        code: Authorization code from OAuth callback (required)
        state: State token containing user_id and session_state_id (required)
        error: Error parameter if Keycloak returned an error
        keycloak: Keycloak service dependency
        ack_state_service: State token service dependency
        vault: Token vault service dependency

    Returns:
        Redirect the user to the consent feedback page

    Raises:
        InvalidAckStateError: If state token is invalid or expired
        KeycloakError: If Keycloak returns an error or code exchange fails
    """

    url = "{config.keycloak.after_consent_redirect_uri}?error={}&description={}"

    if error or error_description:
        return RedirectResponse(url=url.format(error, error_description))

    try:
        state_payload = ack_state_service.parse_ack_state(state)
        token_response = await keycloak.exchange_code_for_token(
            code=code,
            redirect_uri=keycloak.config.consent_redirect_uri,
        )
        user_id = UUID(state_payload.user_id)
        stored_entry = await vault_service.store(
            user_id=user_id,
            token=token_response.refresh_token,
            token_type=TokenType.OFFLINE,
            session_state_id=state_payload.session_state_id,
            attributes=None,
        )
    except AuthManagerError as ex:
        return RedirectResponse(url=url.format(ex.code, ex.message))

    return RedirectResponse(
        url=f"{config.keycloak.after_consent_redirect_uri}",
        headers={"x-persistent-token-id": str(stored_entry.id)},
    )


@router.get(
    "",
    response_model=Ok[OfflineConsentResult],
    status_code=status.HTTP_200_OK,
    summary="Request offline token consent",
    description="Initiates the offline token consent flow by generating a Keycloak authorization url.",
    responses={422: {"model": ValidationErrorResponse}},
)
async def request_offline_token_consent(
    validated_token: ValidatedTokenDep,
    keycloak: KeycloakDep,
    ack_state_service: AckStateDep,
) -> Ok[OfflineConsentResult]:
    """Request user consent for offline access.

    This endpoint validates the access token, extracts user information,
    generates a state token, and constructs a Keycloak authorization URL
    with offline_access scope for user consent.

    Args:
        validated_token: Validated token with user information (validated by dependency)
        keycloak: Keycloak service dependency
        state_token_service: State token service dependency

    Returns:
        OkResponse containing OfflineConsentResponse with consent URL

    Raises:
        UnauthorizedError: If bearer token is missing or invalid
    """

    user_id = str(validated_token.user_id)
    session_state_id = validated_token.session_state_id

    state_token = ack_state_service.make_ack_state(
        user_id=user_id,
        session_state_id=session_state_id,
    )

    authorization_endpoint = f"{keycloak.config.issuer}/realms/{keycloak.config.realm}"
    auth_params = {
        "authorization-endpoint": f"{authorization_endpoint}/protocol/openid-connect/auth",
        "client-id": keycloak.config.client_id,
        "redirect-uri": keycloak.config.consent_redirect_uri,
        "scope": "openid profile email offline_access",
        "state": state_token,
        "nonce": secrets.token_urlsafe(32),  # not required
    }

    consent_url = urls_patterns.URL_AUTH.format(**auth_params)

    return Ok(
        data=OfflineConsentResult(
            consent_url=consent_url,
            session_state_id=session_state_id,
            message="Please visit the consent URL to authorize offline access",
        )
    )
