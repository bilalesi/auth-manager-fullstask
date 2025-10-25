"""FastAPI dependency injection functions.

This module provides dependency injection functions for routes.

"""

from typing import Annotated, AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.base import db_manager
from app.db.repositories.vault import VaultRepository
from app.services.ack_state import AcknowledgementKeycloakStateService
from app.services.encryption import EncryptionService
from app.services.keycloak import KeycloakService
from app.services.vault import VaultService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session, to be used as a dependency."""
    async for session in db_manager.session():
        yield session


def get_encryption_service() -> EncryptionService:
    """Dependency for getting the encryption service."""
    settings = get_settings()
    return EncryptionService(settings.encryption.token_vault_encryption_key)


def get_keycloak_service() -> KeycloakService:
    """Dependency for getting the Keycloak service."""
    settings = get_settings()
    return KeycloakService(settings.keycloak)


def get_ack_state_service() -> AcknowledgementKeycloakStateService:
    """Dependency for getting the state token service."""
    settings = get_settings()
    return AcknowledgementKeycloakStateService(secret_key=settings.ack_state.secret)


SessionDep = Annotated[AsyncSession, Depends(get_db)]
EncryptionDep = Annotated[EncryptionService, Depends(get_encryption_service)]
KeycloakDep = Annotated[KeycloakService, Depends(get_keycloak_service)]
AckStateDep = Annotated[AcknowledgementKeycloakStateService, Depends(get_ack_state_service)]


def get_token_vault_repository(session: SessionDep) -> VaultRepository:
    """Dependency for getting the token vault repository."""
    return VaultRepository(session)


def get_token_vault_service(
    repository: Annotated[VaultRepository, Depends(get_token_vault_repository)],
    encryption: EncryptionDep,
) -> VaultService:
    """Dependency for getting the token vault service."""
    return VaultService(repository, encryption)


TokenVaultRepoDep = Annotated[VaultRepository, Depends(get_token_vault_repository)]
TokenVaultServiceDep = Annotated[VaultService, Depends(get_token_vault_service)]
