"""Pydantic request models."""

from pydantic import UUID4, BaseModel, Field


class AccessTokenRequest(BaseModel):
    """Request model for access token endpoint."""

    id: UUID4 = Field(..., alias="id", description="uuid of the persistent token")


class OfflineTokenRevokeRequest(BaseModel):
    """Request model for offline token revocation."""

    id: UUID4 = Field(..., description="uuid of the token to revoke")


class AckStateTokenPayload(BaseModel):
    """State token payload model."""

    user_id: str
    session_state_id: str


class RefreshTokenPayload(BaseModel):
    """Request model for refresh token."""

    refresh_token: str
