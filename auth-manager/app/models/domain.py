"""Domain models."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import UUID4, AnyUrl, BaseModel, Field

from app.db.models import TokenType


class VaultEntry(BaseModel):
    """Vault entry domain model."""

    id: UUID4
    user_id: UUID4
    token_type: TokenType
    encrypted_token: Optional[str]
    iv: Optional[str]
    token_hash: Optional[str]
    attributes: Optional[dict[str, Any]] = None
    session_state_id: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
        populate_by_name = True


class KeycloakTokenResponse(BaseModel):
    """Keycloak token endpoint response model."""

    access_token: str
    expires_in: int
    refresh_expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    token_type: str
    id_token: Optional[str] = None
    not_before_policy: int = Field(..., alias="not-before-policy")
    scope: Optional[str] = None
    session_state: str


class KeycloakUserSessionResponse(BaseModel):
    """Keycloak user session endpoint response model."""

    id: Optional[str] = Field(default=None, alias="id")
    username: Optional[str] = Field(default=None, alias="username")
    user_id: Optional[str] = Field(default=None, alias="userId")
    ip_address: Optional[str] = Field(default=None, alias="ipAddress")
    start: int = Field(alias="start")
    last_access: int = Field(alias="lastAccess")
    remember_me: bool = Field(alias="rememberMe")
    clients: dict[str, str] = Field(alias="clients")
    transient_user: bool = Field(alias="transientUser")

    class Config:
        populate_by_name = True
        from_attributes = True


class TokenIntrospection(BaseModel):
    active: bool
    exp: Optional[int] = None
    iat: Optional[int] = None
    sub: Optional[UUID] = None
    sid: Optional[str] = None
    scope: Optional[str] = None
    client_id: Optional[str] = None
    username: Optional[str] = None
    token_type: Optional[str] = None


class ValidatedToken(BaseModel):
    """Validated token information from successful introspection.

    This model contains the validated user information extracted from
    a bearer token after successful Keycloak introspection. It is used
    by the token validation dependency to provide type-safe access to
    validated token data in endpoint handlers.

    Attributes:
        user_id: User identifier extracted from the token's 'sub' claim
        session_state_id: Session identifier from the token's 'session_state' claim
        access_token: The original bearer token for potential downstream use
    """

    user_id: UUID4
    session_state_id: str
    access_token: str


class TokenPayload(BaseModel):
    iat: int  # issued at (timestamp)
    jti: str  # jwt id (unique token identifier)
    iss: AnyUrl  # issuer url
    aud: AnyUrl  # audience url
    sub: str  # subject (user id)
    typ: str  # token type ("Offline" | "Refresh")
    azp: Optional[str] = None  # authorized party (client id)
    sid: Optional[str] = None  # session ID
    scope: Optional[str] = None  # scopes (space-separated list)
