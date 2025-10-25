"""Keycloak service using python-keycloak SDK."""

import httpx
from keycloak import KeycloakAdmin, KeycloakGetError, KeycloakOpenID, KeycloakPostError

from app.config import KeycloakSettings
from app.core.exceptions import KeycloakError
from app.models.domain import (
    KeycloakTokenResponse,
    KeycloakUserSessionResponse,
    TokenIntrospection,
    TokenPayload,
)


class KeycloakSDKClient:
    """Keycloak SDK client wrapper."""

    def __init__(self, settings: KeycloakSettings) -> None:
        self.settings = settings
        self._openid_client: KeycloakOpenID | None = None
        self._admin_client: KeycloakAdmin | None = None

    @property
    def openid(self) -> KeycloakOpenID:
        """Get or create OpenID client."""

        if self._openid_client is None:
            self._openid_client = KeycloakOpenID(
                server_url=f"{self.settings.issuer}/",
                client_id=self.settings.client_id,
                realm_name=self.settings.realm,
                client_secret_key=self.settings.client_secret,
                verify=True,
            )
        return self._openid_client

    @property
    def admin(self) -> KeycloakAdmin:
        """Get or create Admin client."""

        if self._admin_client is None:
            self._admin_client = KeycloakAdmin(
                server_url=f"{self.settings.issuer}/",
                client_id=self.settings.client_id,
                realm_name=self.settings.realm,
                client_secret_key=self.settings.client_secret,
            )
        return self._admin_client


class KeycloakService:
    """Service for interacting with Keycloak using python-keycloak SDK."""

    def __init__(self, config: KeycloakSettings) -> None:
        self.config = config
        self.client = KeycloakSDKClient(config)
        self.net = httpx.AsyncClient(timeout=30.0)

    async def refresh_access_token(self, refresh_token: str) -> KeycloakTokenResponse:
        """Refresh access token using refresh token."""
        try:
            result = await self.client.openid.a_refresh_token(refresh_token)
            return KeycloakTokenResponse(**result)
        except KeycloakPostError as e:
            raise KeycloakError(
                "Token refresh failed",
                details={
                    "code": e.response_code,
                    "body": e.response_body,
                },
            ) from e

    async def request_offline_token(self, offline_token: str) -> KeycloakTokenResponse:
        """Request offline token with offline_access scope."""

        try:
            result = await self.client.openid.a_refresh_token(
                grant_type="refresh_token",
                refresh_token=offline_token,
            )
            return KeycloakTokenResponse(**result)
        except KeycloakPostError as e:
            raise KeycloakError(
                "Offline token request failed",
                details={
                    "code": e.response_code,
                    "body": e.response_body,
                },
            ) from e

    async def introspect_token(self, token: str) -> TokenIntrospection:
        """Introspect token to check if it's active."""

        try:
            result = await self.client.openid.a_introspect(token)
            return TokenIntrospection(**result)
        except KeycloakPostError as e:
            raise KeycloakError(
                "Token introspection failed",
                details={
                    "code": e.response_code,
                    "body": e.response_body,
                },
            ) from e

    async def decode_token(self, token: str, validate: bool = False) -> TokenPayload:
        """Introspect token to check if it's active."""

        try:
            result = await self.client.openid.a_decode_token(
                token,
                validate=validate,
            )
            return TokenPayload(**result)
        except KeycloakPostError as e:
            raise KeycloakError(
                "Token introspection failed",
                details={
                    "code": e.response_code,
                    "body": e.response_body,
                },
            ) from e

    async def revoke_session(self, session_id: str) -> None:
        """Revoke Keycloak session using admin API."""

        url = f"{self.config.issuer}/admin/realms/{self.config.realm}/sessions/{session_id}?isOffline=true"
        admin_token = await self._get_admin_token()
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = await self.net.delete(url, headers=headers)

        if response.status_code not in [200, 204]:
            raise KeycloakError(
                message="Session revocation failed",
                details={"error": response.text},
            )

    async def retrieve_user_sessions(self, user_id: str) -> list[KeycloakUserSessionResponse]:
        """Retrieve all user sessions (except offline)"""

        try:
            result = await self.client.admin.a_get_sessions(
                user_id=user_id,
            )
            return [KeycloakUserSessionResponse(**session) for session in result]
        except KeycloakGetError as e:
            raise KeycloakError(
                "Fetch user session failed",
                details={
                    "code": e.response_code,
                    "body": e.response_body,
                },
            ) from e

    async def retrieve_user_offline_sessions(
        self, user_id: str
    ) -> list[KeycloakUserSessionResponse]:
        """Retrieve all offline user sessions per client"""

        url = "{}/admin/realms/{}/users/{}/offline-sessions/{}".format(
            self.config.issuer, self.config.realm, user_id, self.config.client_uuid
        )
        admin_token = await self._get_admin_token()
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = await self.net.get(url, headers=headers)

        if response.status_code not in [200]:
            raise KeycloakError(
                message="Fetch offline sessions failed",
                details={"error": response.text},
            )

        return [KeycloakUserSessionResponse(**session) for session in response.json()]

    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> KeycloakTokenResponse:
        """Exchange authorization code for tokens."""

        try:
            result = await self.client.openid.a_token(
                grant_type="authorization_code",
                code=code,
                redirect_uri=redirect_uri,
            )

            return KeycloakTokenResponse(**result)
        except KeycloakPostError as e:
            raise KeycloakError(
                "Code exchange failed",
                details={
                    "code": e.response_code,
                    "body": e.response_body,
                },
            ) from e

    async def _get_admin_token(self) -> str:
        """Get admin access token for admin API calls."""

        try:
            result = await self.client.openid.a_token(grant_type="client_credentials")
            return result["access_token"]
        except KeycloakPostError as e:
            raise KeycloakError(
                "Admin token request failed",
                details={
                    "code": e.response_code,
                    "body": e.response_body,
                },
            ) from e
