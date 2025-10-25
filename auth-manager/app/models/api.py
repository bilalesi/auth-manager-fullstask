"""Unified API response models."""

from typing import Any, Dict, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Err(BaseModel):
    """Standard error response model."""

    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    reason: Optional[str] = Field(default=None, description="Extra error reason or context")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Extra error details")


class Ok(BaseModel, Generic[T]):
    """Standard success response wrapper."""

    data: T = Field(..., description="Response data")
