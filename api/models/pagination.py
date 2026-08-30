"""
Shared response envelope for paginated list endpoints.

Every future list endpoint (e.g. GET /api/v1/players, GET /api/v1/courses)
returns this shape rather than a bare list, so a client can always find the
total row count and the limit/offset it was given back, regardless of
which resource it's listing.
"""

from typing import Any

from pydantic import BaseModel


class PaginatedResponse(BaseModel):
    total: int
    limit: int
    offset: int
    # `list[Any]` for now -- each endpoint narrows this to its own response
    # model (e.g. `list[CourseOut]`) via a subclass or a generic once
    # per-resource models exist. Left untyped here rather than guessing at
    # a shape that isn't defined yet.
    results: list[Any]
