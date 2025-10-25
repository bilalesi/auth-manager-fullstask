import uuid
from functools import cache
from typing import List

from pydantic import (
    AnyHttpUrl,
    Field,
    PostgresDsn,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    url: PostgresDsn | None = Field(None, description="PostgreSQL database URL with asyncpg driver")
    engine: str | None = Field(
        "postgresql+asyncpg", description="PostgreSQL database URL with asyncpg driver"
    )
    username: str = "auth_manager"
    password: str = "auth_manager"
    name: str = "auth_manager"
    host: str = "db"
    port: int = 5432

    pool_size: int = Field(default=10, ge=1, le=100, description="Database connection pool size")
    max_overflow: int = Field(
        default=20,
        ge=0,
        le=100,
        description="Maximum number of connections that can be created beyond pool_size",
    )
    pool_timeout: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Timeout in seconds for getting a connection from the pool",
    )
    echo: bool = Field(default=False, description="Enable SQLAlchemy query logging")

    @model_validator(mode="after")
    def make_database_connection_string(self) -> "DatabaseSettings":
        """Build database URL from components if not provided."""
        if self.url is None:
            dsn = PostgresDsn.build(
                scheme=self.engine,
                username=self.username,
                password=self.password,
                host=self.host,
                port=self.port,
                path=self.name,
            )
            self.url = dsn.unicode_string()
        return self

    model_config = SettingsConfigDict(
        env_prefix="DATABASE_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class KeycloakSettings(BaseSettings):
    """Keycloak OAuth/OIDC configuration settings."""

    issuer: str = Field(..., description="Keycloak issuer URL")
    client_id: str = Field(..., description="Keycloak client ID")
    client_uuid: uuid.UUID = Field(..., description="Keycloak client UUID")
    client_secret: str = Field(..., description="Keycloak client secret")
    realm: str = Field(..., description="Keycloak realm name")
    consent_redirect_uri: AnyHttpUrl = Field(
        ..., description="Redirect url after consent confirmed by the user"
    )
    after_consent_redirect_uri: AnyHttpUrl = Field(
        ..., description="Redirect url after consent confirmed by the user"
    )

    model_config = SettingsConfigDict(
        env_prefix="KEYCLOAK_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class EncryptionSettings(BaseSettings):
    """Token encryption configuration settings."""

    token_vault_encryption_key: str = Field(
        ...,
        min_length=64,
        max_length=64,
        description="64-character hex string (32 bytes) for AES-256 encryption",
    )

    @field_validator("token_vault_encryption_key")
    @classmethod
    def validate_encryption_key(cls, v: str) -> str:
        """Validate that the encryption key is a valid 64-character hex string."""
        if len(v) != 64:
            raise ValueError("Encryption key must be exactly 64 characters")

        try:
            bytes.fromhex(v)
        except ValueError:
            raise ValueError("Encryption key must be a valid hexadecimal string")

        return v

    model_config = SettingsConfigDict(
        env_prefix="AUTH_MANAGER_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class AckStateSettings(BaseSettings):
    """State token configuration settings."""

    secret: str = Field(..., min_length=32, description="Secret key for signing state tokens")
    expiry: int = Field(
        default=60,
        ge=60,
        le=3600,
        description="State token expiry time in seconds (default: 120 minutes)",
    )

    model_config = SettingsConfigDict(
        env_prefix="ACK_STATE_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class CORSSettings(BaseSettings):
    """CORS configuration settings."""

    origins: str = Field(
        default="http://localhost:3000", description="Comma-separated allowed CORS origins"
    )
    allow_credentials: bool = Field(default=True, description="Allow credentials in CORS requests")

    @property
    def origins_list(self) -> List[str]:
        """Get origins as a list."""
        if isinstance(self.origins, str):
            return [origin.strip() for origin in self.origins.split(",") if origin.strip()]
        return [self.origins]

    model_config = SettingsConfigDict(
        env_prefix="CORS_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class AppSettings(BaseSettings):
    """Main application settings that aggregates all configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_nested_delimiter="__",
    )

    app_name: str = Field(default="Auth Manager Service", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(
        default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    port: int = Field(default=8000, ge=1, le=65535, description="Application port")
    commit_sha: str | None = Field(default=None, description="Commit hash")
    env: str = Field(default="dev", description="Working environment")
    root_path: str = Field(default="", description="Root path")
    docs_favicon_url: str = Field(
        default="https://s3.amazonaws.com/staging.openbraininstitute.org/static/favicon.ico",
        description="Favicon icon",
    )
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    keycloak: KeycloakSettings = Field(default_factory=KeycloakSettings)
    encryption: EncryptionSettings = Field(default_factory=EncryptionSettings)
    ack_state: AckStateSettings = Field(default_factory=AckStateSettings)
    cors: CORSSettings = Field(default_factory=CORSSettings)

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in allowed_levels:
            raise ValueError(f"Log level must be one of {allowed_levels}, got '{v}'")
        return v_upper


_settings: AppSettings | None = None


@cache
def get_settings() -> AppSettings:
    """
    Get the global settings instance.

    This function implements a singleton pattern to ensure settings
    are loaded only once and reused across the application.

    Returns:
        AppSettings: The application settings instance

    Raises:
        ValidationError: If required environment variables are missing or invalid
    """
    global _settings
    if _settings is None:
        _settings = AppSettings()
    return _settings
