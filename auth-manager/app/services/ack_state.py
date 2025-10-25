"""State token generation and parsing service."""

from datetime import datetime, timedelta, timezone

import jwt

from app.core.exceptions import InvalidAckStateError
from app.models.request import AckStateTokenPayload


class AcknowledgementKeycloakStateService:
    """Service for generating and parsing JWT state tokens."""

    def __init__(self, secret_key: str):
        """Initialize state token service.

        Args:
            secret_key: Secret key for signing JWT tokens
        """
        self.secret_key = secret_key

    def make_ack_state(
        self,
        user_id: str,
        session_state_id: str,
        expires_in: int = 600,  # 10 minutes default
    ) -> str:
        """Generate JWT state token.

        Args:
            user_id: User identifier
            session_state_id: Keycloak session state identifier
            expires_in: Token expiration time in seconds (default: 600 = 10 minutes)

        Returns:
            JWT token string
        """
        now = datetime.now(timezone.utc)
        payload = {
            "user_id": user_id,
            "session_state_id": session_state_id,
            "exp": now + timedelta(seconds=expires_in),
            "iat": now,
        }

        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def parse_ack_state(self, token: str) -> AckStateTokenPayload:
        """Parse and validate state token without checking expiration."""

        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=["HS256"],
                options={"verify_exp": False},
            )
            return AckStateTokenPayload(
                user_id=payload["user_id"], session_state_id=payload["session_state_id"]
            )
        except jwt.InvalidTokenError as e:
            raise InvalidAckStateError("Invalid state token") from e
        except KeyError as e:
            raise InvalidAckStateError("Missing required field in state token") from e
        except Exception as e:
            raise InvalidAckStateError("Unknown error decoding ack state") from e
