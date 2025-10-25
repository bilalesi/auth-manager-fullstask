"""Token vault repository for database operations."""

from typing import List, Optional, cast
from uuid import UUID

from sqlalchemy import CursorResult, select, update
from sqlalchemy import delete as db_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models import AuthVault, TokenType
from app.models.domain import VaultEntry

logger = get_logger(__name__)


class VaultRepository:
    """Repository for token vault database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: UUID,
        token_type: TokenType,
        encrypted_token: str,
        iv: str,
        token_hash: str,
        session_state_id: str,
        attributes: Optional[dict] = None,
    ) -> VaultEntry:
        """Create a new token vault entry."""

        entry = AuthVault(
            user_id=user_id,
            token_type=token_type,
            encrypted_token=encrypted_token,
            iv=iv,
            token_hash=token_hash,
            session_state_id=session_state_id,
            attributes=attributes,
        )
        self.session.add(entry)
        await self.session.flush()
        await self.session.refresh(entry)

        return VaultEntry.model_validate(entry)

    async def upsert_refresh_token(
        self,
        user_id: UUID,
        encrypted_token: str,
        iv: str,
        token_hash: str,
        session_state_id: str,
        attributes: Optional[dict] = None,
    ) -> str:
        """Upsert refresh token (ensure only one per user)."""

        existing = await self.retrieve_by_user_id(user_id, TokenType.REFRESH)

        if existing:
            await self.session.execute(
                update(AuthVault)
                .where(AuthVault.id == existing.id)
                .values(
                    encrypted_token=encrypted_token,
                    iv=iv,
                    token_hash=token_hash,
                    session_state_id=session_state_id,
                    attributes=attributes,
                )
            )
            return str(existing.id)
        else:
            entry = await self.create(
                user_id=user_id,
                token_type=TokenType.REFRESH,
                encrypted_token=encrypted_token,
                iv=iv,
                token_hash=token_hash,
                session_state_id=session_state_id,
                attributes=attributes,
            )
            return str(entry.id)

    async def delete(self, id: UUID) -> bool:
        """Delete token by ID."""

        stmt = db_delete(AuthVault).where(AuthVault.id == id)
        result = await self.session.execute(stmt)
        await self.session.flush()

        return cast(CursorResult, result).rowcount > 0

    async def retrieve(self, token_id: UUID) -> VaultEntry:
        """Retrieve token by persistent token ID."""

        result = await self.session.execute(select(AuthVault).where(AuthVault.id == token_id))
        entry = result.scalar_one()

        return VaultEntry.model_validate(entry)

    async def retrieve_by_user_id(
        self, user_id: UUID, token_type: Optional[TokenType] = None
    ) -> Optional[VaultEntry]:
        """Get token by user ID and optionally token type."""

        query = select(AuthVault).where(AuthVault.user_id == user_id)
        if token_type:
            query = query.where(AuthVault.token_type == token_type)
        query = query.order_by(AuthVault.created_at.desc())

        result = await self.session.execute(query)
        entry = result.scalar_one_or_none()
        return VaultEntry.model_validate(entry) if entry else None

    async def retrieve_by_session_state_or_panic(
        self,
        session_state_id: str,
        token_type: Optional[TokenType] = None,
    ) -> VaultEntry:
        """Get token by session state ID."""

        query = select(AuthVault).where(AuthVault.session_state_id == session_state_id)
        if token_type:
            query = query.where(AuthVault.token_type == token_type)

        result = await self.session.execute(query)
        entry = result.scalar_one()

        return VaultEntry.model_validate(entry)

    async def retrieve_by_session_state_id(
        self,
        session_state_id: str,
        token_type: Optional[TokenType] = None,
    ) -> VaultEntry | None:
        """Get token by session state ID."""

        query = select(AuthVault).where(AuthVault.session_state_id == session_state_id)
        if token_type:
            query = query.where(AuthVault.token_type == token_type)

        result = await self.session.execute(query)
        entry = result.scalar_one_or_none()

        return VaultEntry.model_validate(entry) if entry else None

    async def retrieve_all_by_session_state_id(
        self,
        session_state_id: str,
        exclude_id: Optional[UUID] = None,
        token_type: Optional[TokenType] = None,
    ) -> List[VaultEntry]:
        """Get all tokens with matching session state ID."""

        query = select(AuthVault).where(AuthVault.session_state_id == session_state_id)
        if exclude_id:
            query = query.where(AuthVault.id != exclude_id)
        if token_type:
            query = query.where(AuthVault.token_type == token_type)

        result = await self.session.execute(query)
        entries = result.scalars().all()
        return [VaultEntry.model_validate(e) for e in entries]
