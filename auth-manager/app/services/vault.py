"""Token vault service for managing encrypted token storage."""

from typing import Optional
from uuid import UUID

from app.core.exceptions import DatabaseError, TokenNotFoundError, ValidationError
from app.core.guards import guard_invariant, guard_raise_if_not_found
from app.core.logging import get_logger
from app.db.models import TokenType
from app.db.repositories.vault import VaultRepository
from app.models.domain import VaultEntry
from app.services.encryption import EncryptionService

logger = get_logger(__name__)


class VaultService:
    """Managing encrypted token storage and retrieval."""

    def __init__(self, repository: VaultRepository, encryption: EncryptionService):
        self.repository = repository
        self.encryption = encryption

    async def store(
        self,
        user_id: UUID,
        token: str,
        token_type: TokenType,
        session_state_id: str,
        attributes: Optional[dict] = None,
    ) -> VaultEntry:
        """Encrypt and store a token.

        Args:
            user_id: User identifier
            token: Token string to encrypt and store
            token_type: Type of token (offline or refresh)
            session_state_id: Keycloak session state identifier
            attributes: Optional metadata to store with token

        Returns:
            VaultEntry with stored token information
        """

        iv = self.encryption.generate_iv()
        encrypted_token = self.encryption.encrypt_token(token, iv)
        token_hash = self.encryption.hash_token(token)

        result = await self.repository.create(
            user_id=user_id,
            token_type=token_type,
            encrypted_token=encrypted_token,
            iv=iv,
            token_hash=token_hash,
            session_state_id=session_state_id,
            attributes=attributes,
        )

        return result

    async def retrieve_and_decrypt(
        self,
        token_id: UUID,
    ) -> tuple[VaultEntry, str]:
        """Retrieve and decrypt a token.

        Args:
            token_id: Persistent token ID (UUID)

        Returns:
            Tuple of (VaultEntry, decrypted_token_string)

        Raises:
            TokenNotFoundError: If token not found or has no encrypted data
        """

        with guard_raise_if_not_found(TokenNotFoundError("Token not found")):
            entry = await self.repository.retrieve(token_id)

        with guard_invariant(
            entry,
            lambda e: not e.encrypted_token or not e.iv,
            TokenNotFoundError("Token has no encrypted data"),
        ) as en:
            assert en.encrypted_token is not None
            assert en.iv is not None
            decrypted_token = self.encryption.decrypt_token(en.encrypted_token, en.iv)

        return entry, decrypted_token

    async def upsert_refresh_token(
        self,
        user_id: UUID,
        token: str,
        session_state_id: str,
        attributes: Optional[dict] = None,
    ) -> str:
        """Upsert refresh token (only one per user).

        Args:
            user_id: User identifier
            token: Refresh token string
            session_state_id: Keycloak session state identifier
            attributes: Optional metadata to store with token

        Returns:
            Persistent token ID (UUID as string)
        """

        iv = self.encryption.generate_iv()
        encrypted_token = self.encryption.encrypt_token(token, iv)
        token_hash = self.encryption.hash_token(token)

        return await self.repository.upsert_refresh_token(
            user_id=user_id,
            encrypted_token=encrypted_token,
            iv=iv,
            token_hash=token_hash,
            session_state_id=session_state_id,
            attributes=attributes,
        )

    async def retrieve_by_session_state_id_or_panic(
        self,
        session_state_id: str,
        token_type: Optional[TokenType] = None,
    ) -> tuple[VaultEntry, str] | None:
        """
        Retrieves and decrypts a token entry by session state ID

        Args:
            session_state_id: The session state identifier to look up.
            token_type: Optional token type to filter the search.

        Returns:
            tuple[VaultEntry, str] | None: A tuple containing:
                - The vault entry with the encrypted token
                - The decrypted token string
            Returns None if no matching entry is found.

        Raises:
            DatabaseError: If no token is found for the given session state ID and token type.
            TokenNotFoundError: If the found entry has missing encryption data.
        """

        with guard_raise_if_not_found(
            DatabaseError("No token found for the session/type requested", "entity_not_found"),
        ):
            entry = await self.repository.retrieve_by_session_state_or_panic(
                session_state_id, token_type
            )

        with guard_invariant(
            entry,
            lambda e: not e.encrypted_token or not e.iv,
            TokenNotFoundError(
                "Token has no encrypted data",
            ),
        ) as e:
            assert e.encrypted_token is not None
            assert e.iv is not None
            decrypted_token = self.encryption.decrypt_token(e.encrypted_token, e.iv)
            return entry, decrypted_token

    async def retrieve_by_session_state_id(
        self,
        session_state_id: str,
        token_type: Optional[TokenType] = None,
    ) -> tuple[VaultEntry, str] | None:
        """Retrieves and decrypt token by session state ID.

        Args:
            session_state_id: Keycloak session state identifier
            token_type: Optional token type filter

        Returns:
            Tuple of (VaultEntry, decrypted_token_string) or None if not found
        """

        entry = await self.repository.retrieve_by_session_state_id(session_state_id, token_type)

        if entry:
            assert entry.encrypted_token is not None
            assert entry.iv is not None
            decrypted_token = self.encryption.decrypt_token(entry.encrypted_token, entry.iv)
            return entry, decrypted_token

        return None

    async def retrieve_by_user_id(
        self, user_id: UUID, token_type: Optional[TokenType] = None
    ) -> Optional[tuple[VaultEntry, str]]:
        """Retrieves and decrypt token by user ID.

        Args:
            user_id: User identifier
            token_type: Optional token type filter

        Returns:
            Tuple of (VaultEntry, decrypted_token) or None if not found
        """

        with guard_raise_if_not_found(DatabaseError("No Token found for the user/type requested")):
            entry = await self.repository.retrieve_by_user_id(user_id, token_type)
            assert entry

        with guard_invariant(
            entry,
            lambda e: not e.encrypted_token or not e.iv,
            ValidationError(
                "Token has no encrypted data",
            ),
        ) as en:
            assert en.encrypted_token is not None
            assert en.iv is not None
            decrypted_token = self.encryption.decrypt_token(en.encrypted_token, en.iv)
            return en, decrypted_token

    async def delete_token(
        self,
        token_id: UUID,
    ) -> bool:
        """Delete a token from vault.

        Args:
            token_id: Persistent token ID (UUID)

        Returns:
            True if token was deleted, False if not found
        """

        return await self.repository.delete(token_id)

    async def is_token_shared(
        self, session_state_id: str, exclude_id: UUID, token_type: TokenType | None = None
    ) -> bool:
        """Check if token is shared by hash or session.

        Args:
            token_hash: SHA-256 hash of the token
            session_state_id: Keycloak session state identifier
            exclude_id: Token ID to exclude from search

        Returns:
            Boolean has_shared_session
        """

        shared_sessions = await self.repository.retrieve_all_by_session_state_id(
            session_state_id,
            exclude_id=exclude_id,
            token_type=token_type,
        )

        return len(shared_sessions) > 0
