"""Pydantic response models."""

from pydantic import UUID4, BaseModel, Field


class AccessTokenResult(BaseModel):
    """Response model for access token endpoint."""

    access_token: str = Field(..., description="The new access token")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class OfflineTokenResult(BaseModel):
    """Response model for offline token endpoints."""

    persistent_token_id: UUID4 = Field(..., description="UUID identifier for the stored token")
    session_state_id: str = Field(..., description="Keycloak session state identifier")


class RefreshTokenIdResult(BaseModel):
    """Response model for refresh token ID endpoint."""

    id: str = Field(..., description="UUID identifier for the stored refresh token")


class OfflineConsentResult(BaseModel):
    """Response model for offline token consent request."""

    consent_url: str = Field(..., description="URL to redirect user for consent")
    session_state_id: str = Field(..., description="Keycloak session state identifier")
    message: str = Field(..., description="Informational message for the user")


class TokenValidationResponse(BaseModel):
    """Response model for token validation endpoint."""

    valid: bool = Field(default=True, description="Whether the token is valid and active")


class OfflineTokenRevocationResponse(BaseModel):
    """Response model for offline token revocation endpoint."""

    message: str = Field(..., description="Success message")
    persistent_token_id: UUID4 = Field(..., description="UUID of the revoked token")
    token_deleted: bool = Field(..., description="Whether the token was revoked in Keycloak")
    session_revoked: bool = Field(..., description="Whether the Keycloak session was revoked")
    had_shared_session: bool = Field(
        ..., description="Whether other tokens shared the same session state"
    )


class ValidationErrorResponse(BaseModel):
    error: str
    code: str
    reason: str
    details: dict[str, str]


class VersionResponse(BaseModel):
    app_name: str | None
    app_version: str | None
    database_version: str | None
    commit_sha: str | None
    env: str | None
