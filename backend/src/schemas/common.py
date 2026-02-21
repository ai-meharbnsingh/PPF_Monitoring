"""
Module: common.py
Purpose:
    Shared Pydantic schemas used across multiple route modules.
    PaginatedResponse, SuccessResponse, ErrorResponse, and list wrappers.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


# ─── Generic Paginated Response ───────────────────────────────────────────────
class PaginatedResponse(BaseModel, Generic[DataT]):
    """Wrapper for paginated list endpoints."""

    items: List[DataT]
    total: int = Field(..., description="Total records matching the query")
    page: int = Field(..., ge=1, description="Current page number (1-indexed)")
    page_size: int = Field(..., ge=1, le=200, description="Records per page")
    total_pages: int = Field(..., ge=0)
    has_next: bool
    has_prev: bool


# ─── Standard Success / Error ──────────────────────────────────────────────────
class SuccessResponse(BaseModel):
    """Simple success acknowledgement for actions that return no data."""

    success: bool = True
    message: str


class ErrorDetail(BaseModel):
    field: Optional[str] = None
    message: str


class ErrorResponse(BaseModel):
    """Standard error envelope."""

    success: bool = False
    error_code: str
    message: str
    details: Optional[List[ErrorDetail]] = None


# ─── Pagination helper ────────────────────────────────────────────────────────
def build_paginated(
    items: list,
    total: int,
    page: int,
    page_size: int,
) -> dict:
    """Build pagination metadata dict for use in route handlers."""
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
    }
