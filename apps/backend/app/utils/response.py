"""
Standard API Response Wrapper - ICFES Leveling
Provides a consistent response format across all API endpoints.

Format:
{
    "success": bool,
    "data": any,
    "meta": {
        "timestamp": "ISO8601 string",
        "version": "1.0",
        ...additional meta fields
    }
}
"""

from datetime import datetime
from typing import Any, Dict, Generic, Optional, TypeVar
from pydantic import BaseModel, Field


# ============================================
# PYDANTIC MODELS FOR TYPE SAFETY
# ============================================

T = TypeVar("T")


class ResponseMeta(BaseModel):
    """Metadata included in all API responses"""
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    version: str = "1.0"
    request_id: Optional[str] = None

    class Config:
        extra = "allow"  # Allow additional metadata fields


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response wrapper"""
    success: bool
    data: Optional[T] = None
    meta: ResponseMeta = Field(default_factory=ResponseMeta)

    class Config:
        extra = "forbid"


class ErrorDetail(BaseModel):
    """Error details for error responses"""
    code: Optional[str] = None
    message: str
    field: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = False
    data: None = None
    error: ErrorDetail
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


# ============================================
# HELPER FUNCTIONS
# ============================================

def api_response(
    success: bool,
    data: Any = None,
    meta: Optional[Dict[str, Any]] = None,
    **extra_meta
) -> Dict[str, Any]:
    """
    Create a standard API response.

    Args:
        success: Whether the request was successful
        data: The response data (any type)
        meta: Optional dictionary of metadata to include
        **extra_meta: Additional metadata fields as keyword arguments

    Returns:
        Dictionary in standard response format

    Example:
        >>> api_response(True, {"user_id": "123"})
        {
            "success": True,
            "data": {"user_id": "123"},
            "meta": {"timestamp": "2024-01-15T10:30:00Z", "version": "1.0"}
        }

        >>> api_response(True, users, count=len(users), page=1)
        {
            "success": True,
            "data": [...],
            "meta": {"timestamp": "...", "version": "1.0", "count": 10, "page": 1}
        }
    """
    response_meta = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0"
    }

    # Merge additional metadata
    if meta:
        response_meta.update(meta)
    if extra_meta:
        response_meta.update(extra_meta)

    return {
        "success": success,
        "data": data,
        "meta": response_meta
    }


def success_response(
    data: Any = None,
    meta: Optional[Dict[str, Any]] = None,
    **extra_meta
) -> Dict[str, Any]:
    """
    Create a successful API response.

    Args:
        data: The response data
        meta: Optional metadata dictionary
        **extra_meta: Additional metadata fields

    Returns:
        Dictionary in standard response format with success=True

    Example:
        >>> success_response({"id": "123", "name": "Test"})
        {"success": True, "data": {...}, "meta": {...}}
    """
    return api_response(True, data, meta, **extra_meta)


def error_response(
    message: str,
    code: Optional[str] = None,
    field: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
    **extra_meta
) -> Dict[str, Any]:
    """
    Create an error API response.

    Args:
        message: Human-readable error message
        code: Optional error code (e.g., "VALIDATION_ERROR")
        field: Optional field name that caused the error
        meta: Optional metadata dictionary
        **extra_meta: Additional metadata fields

    Returns:
        Dictionary in standard error response format

    Example:
        >>> error_response("User not found", code="NOT_FOUND")
        {
            "success": False,
            "data": None,
            "error": {"code": "NOT_FOUND", "message": "User not found"},
            "meta": {...}
        }
    """
    response_meta = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0"
    }

    if meta:
        response_meta.update(meta)
    if extra_meta:
        response_meta.update(extra_meta)

    error_detail = {"message": message}
    if code:
        error_detail["code"] = code
    if field:
        error_detail["field"] = field

    return {
        "success": False,
        "data": None,
        "error": error_detail,
        "meta": response_meta
    }


def paginated_response(
    data: Any,
    total: int,
    limit: int,
    offset: int,
    meta: Optional[Dict[str, Any]] = None,
    **extra_meta
) -> Dict[str, Any]:
    """
    Create a paginated API response.

    Args:
        data: The list of items
        total: Total number of items
        limit: Items per page
        offset: Current offset
        meta: Optional additional metadata
        **extra_meta: Additional metadata fields

    Returns:
        Dictionary with pagination metadata

    Example:
        >>> paginated_response(users, total=100, limit=10, offset=0)
        {
            "success": True,
            "data": [...],
            "meta": {
                "timestamp": "...",
                "version": "1.0",
                "pagination": {
                    "total": 100,
                    "limit": 10,
                    "offset": 0,
                    "has_more": True
                }
            }
        }
    """
    pagination_meta = {
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total
    }

    response_meta = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0",
        "pagination": pagination_meta
    }

    if meta:
        response_meta.update(meta)
    if extra_meta:
        response_meta.update(extra_meta)

    return {
        "success": True,
        "data": data,
        "meta": response_meta
    }
