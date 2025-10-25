import enum
import uuid
from datetime import datetime
from typing import ClassVar, Optional

from sqlalchemy import (
    DateTime,
    Index,
    MetaData,
    Text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)
from sqlalchemy.sql import func


class TokenType(str, enum.Enum):
    """Token type enumeration."""

    OFFLINE = "offline"
    REFRESH = "refresh"


class Base(DeclarativeBase):
    type_annotation_map: ClassVar[dict] = {
        datetime: DateTime(timezone=True),
    }
    # See https://alembic.sqlalchemy.org/en/latest/naming.html
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


class AuthVault(Base):
    """Auth vault table for storing encrypted tokens."""

    __tablename__ = "auth_vault"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    token_type: Mapped[TokenType] = mapped_column(
        SQLEnum(TokenType, name="auth_token_type"), nullable=False
    )
    encrypted_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    iv: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    token_hash: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attributes: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    session_state_id: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    __table_args__ = (
        Index("auth_vault_user_id_token_type_idx", "user_id", "token_type"),
        Index("auth_vault_session_state_token_type_idx", "session_state_id", "token_type"),
    )

    def __repr__(self):
        return f"<AuthVault(id={self.id}, user_id={self.user_id}, token_type={self.token_type})>"
