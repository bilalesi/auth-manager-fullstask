"""Health check endpoints."""

from fastapi import APIRouter, status
from sqlalchemy import text
from starlette.responses import RedirectResponse, Response
from starlette.status import HTTP_302_FOUND

from app.config import get_settings
from app.core.logging import get_logger
from app.dependencies import KeycloakDep, SessionDep
from app.models.api import Ok
from app.models.response import VersionResponse

logger = get_logger(__name__)

router = APIRouter(tags=["service"])
config = get_settings()


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> str:
    """Basic health check endpoint."""
    logger.debug("health_check")
    return "OK"


@router.get(
    "/version",
)
async def version(db: SessionDep, kc: KeycloakDep) -> Ok[VersionResponse]:
    """Version endpoint providing basic service information."""
    result = await db.execute(text("SELECT version();"))
    database_version = result.scalar_one()

    return Ok(
        data=VersionResponse(
            app_name=config.app_name,
            app_version=config.app_version,
            database_version=database_version,
            commit_sha=config.commit_sha,
            env=config.env,
        )
    )


@router.get("/", include_in_schema=False)
async def root() -> Response:
    """Root endpoint."""
    return RedirectResponse(
        url=f"{config.root_path}/sdocs",
        status_code=HTTP_302_FOUND,
    )
