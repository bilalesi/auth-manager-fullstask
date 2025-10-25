"""API v1 routes."""

from fastapi import APIRouter

from app.api.v1 import (
    access_token,
    offline_token,
    offline_token_id,
    refresh_token,
    refresh_token_id,
    validate_token,
)

router = APIRouter(prefix="/v1", tags=["auth-manager"])

router.include_router(access_token.router)
router.include_router(offline_token.router)
router.include_router(offline_token_id.router)
router.include_router(refresh_token_id.router)
router.include_router(validate_token.router)
router.include_router(refresh_token.router)

__all__ = [
    "router",
    "access_token",
    "offline_token",
    "offline_token_id",
    "refresh_token_id",
    "validate_token",
    "refresh_token",
]
