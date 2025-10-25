"""Security utilities and dependencies."""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import InvalidRequestError, TokenNotActiveError, UnauthorizedError
from app.core.guards import guard_invariant
from app.core.logging import get_logger
from app.dependencies import get_keycloak_service
from app.models.domain import ValidatedToken
from app.services.keycloak import KeycloakService

logger = get_logger(__name__)


bearer_scheme = HTTPBearer(auto_error=False)


async def get_bearer_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> str:
    """Extract and validate Bearer token from Authorization header.

    Args:
        credentials: HTTP authorization credentials from FastAPI

    Returns:
        str: The extracted bearer token

    Raises:
        UnauthorizedError: If credentials are missing or invalid

    """

    with guard_invariant(
        credentials, lambda e: e is None, UnauthorizedError("Authorization header is required")
    ):
        assert credentials is not None
        with guard_invariant(
            credentials,
            lambda e: "scheme" in e and e.scheme.lower() != "bearer",
            UnauthorizedError(
                "Invalid authentication scheme. Expected: Bearer",
            ),
        ):
            pass

    return credentials.credentials


BearerToken = Annotated[str, Depends(get_bearer_token)]


async def get_validated_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    keycloak: Annotated[KeycloakService, Depends(get_keycloak_service)],
) -> ValidatedToken:
    """Validate bearer token and extract user information.

    Args:
        credentials: HTTP authorization credentials from bearer_scheme
        keycloak: Keycloak service for token introspection

    Returns:
        ValidatedToken: Validated token data with user information

    Raises:
        UnauthorizedError: If token is missing, invalid, or not active
        TokenNotActiveError: If token is not active
        KeycloakError: If introspection fails

    """

    with guard_invariant(
        credentials, lambda e: e is None, UnauthorizedError("Authorization header is required")
    ):
        assert credentials is not None
        with guard_invariant(
            credentials,
            lambda e: "scheme" in e and e.scheme.lower() != "bearer",
            "Invalid authentication scheme. Expected: Bearer",
        ):
            pass

    bearer_token = credentials.credentials
    token_info = await keycloak.introspect_token(bearer_token)

    with guard_invariant(
        token_info,
        lambda e: not e.active,
        TokenNotActiveError("Token is not active", "token_not_active"),
    ):
        ...

    with guard_invariant(
        token_info,
        lambda e: e.sub is None,
        InvalidRequestError("Token missing required claim: sub"),
    ):
        assert token_info.sub is not None
        user_id = token_info.sub

    with guard_invariant(
        token_info,
        lambda e: e.sid is None,
        InvalidRequestError("Token missing required claim: session_state"),
    ):
        assert token_info.sid is not None
        return ValidatedToken(
            user_id=user_id,
            session_state_id=token_info.sid,
            access_token=bearer_token,
        )


ValidatedTokenDep = Annotated[ValidatedToken, Depends(get_validated_token)]
