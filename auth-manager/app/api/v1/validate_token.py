"""Token validation endpoint."""

from fastapi import APIRouter, status

from app.core.exceptions import TokenNotActiveError
from app.core.guards import guard_invariant
from app.core.logging import get_logger
from app.core.security import BearerToken
from app.dependencies import KeycloakDep
from app.models.api import Ok
from app.models.response import TokenValidationResponse, ValidationErrorResponse

logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "/validate-token",
    response_model=Ok[TokenValidationResponse],
    status_code=status.HTTP_200_OK,
    summary="Validate access token",
    description="Validates an access token by introspecting it with Keycloak.",
    responses={422: {"model": ValidationErrorResponse}},
)
async def validate_token(
    token: BearerToken,
    keycloak: KeycloakDep,
) -> Ok[TokenValidationResponse]:
    """Validate an access token via Keycloak introspection."""

    introspection_result = await keycloak.introspect_token(token)

    with guard_invariant(
        introspection_result,
        lambda e: not e.active,
        TokenNotActiveError("Token is not active"),
    ):
        pass

    return Ok(data=TokenValidationResponse(valid=True))
