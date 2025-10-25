from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError as PydanticValidationError
from scalar_fastapi import Layout, get_scalar_api_reference

from app.api import health
from app.api.v1 import router as v1_router
from app.config import get_settings
from app.core.exceptions import AuthManagerError
from app.core.exceptions_handler import (
    auth_manager_error_handler,
    generic_exception_handler,
    pydantic_validation_error_handler,
    request_validation_error_handler,
)
from app.core.logging import configure_logging, get_logger
from app.db.base import db_manager
from app.middleware import LoggingMiddleware, RequestIDMiddleware

logger = get_logger(__name__)


config = get_settings()


def make_logger():
    configure_logging(config.log_level)
    logger.info("logger_initialized", log_level=config.log_level)


def make_database():
    """Initialize database connection."""
    db_manager.init(
        database_url=str(config.database.url),
        pool_size=config.database.pool_size,
        max_overflow=config.database.max_overflow,
        pool_timeout=config.database.pool_timeout,
        echo=config.database.echo,
    )
    logger.info("database_initialized")


@asynccontextmanager
async def lifespan(app: FastAPI):
    make_logger()
    make_database()

    yield

    logger.info("shutdown_started")
    await db_manager.close()
    logger.info("shutdown_complete")


def configure_cors():
    """Configure CORS middleware with settings from environment."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors.origins_list,
        allow_credentials=config.cors.allow_credentials,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )


app = FastAPI(
    title=config.app_name,
    version=config.app_version,
    debug=config.debug,
    description=(
        """
> Keycloak token management microservice for secure storage and retrieval \n
> of OAuth tokens including refresh tokens, offline tokens, and access token generation.
        """
    ),
    exception_handlers={
        AuthManagerError: auth_manager_error_handler,
        RequestValidationError: request_validation_error_handler,
        PydanticValidationError: pydantic_validation_error_handler,
        Exception: generic_exception_handler,
    },
    lifespan=lifespan,
    root_path=config.root_path,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    redirect_slashes=False,
)


app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestIDMiddleware)

app.include_router(health.router)
app.include_router(v1_router)


@app.get("/sdocs", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        title=config.app_name,
        layout=Layout.CLASSIC,
        openapi_url=app.openapi_url,
        hide_client_button=True,
        hide_download_button=True,
        scalar_favicon_url=config.docs_favicon_url,
        show_sidebar=False,
    )
