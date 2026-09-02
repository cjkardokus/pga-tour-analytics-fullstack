"""
Shared response envelope for paginated list endpoints.

Every list endpoint's browse mode (GET /api/v1/players, GET /api/v1/courses,
GET /api/v1/leaderboards/season/{year} and /all-time) returns this shape
rather than a bare list, so a client can always find the total row count
and the limit/offset it was given back, regardless of which resource it's
listing.
"""

from typing import Any

from pydantic import BaseModel


class PaginatedResponse(BaseModel):
    total: int
    limit: int
    offset: int
    # `list[Any]`, deliberately never narrowed to a per-resource model (e.g.
    # `list[CourseResponse]`) via a subclass or a generic: each router
    # already builds its `results` list from that resource's own model (see
    # api/routers/*.py), so the runtime shape is correct either way -- this
    # field just isn't declared precisely enough for FastAPI's OpenAPI
    # schema to describe it. That has a real downstream cost:
    # openapi-typescript can only generate `unknown[]` for this field, so
    # the front-end hand-writes its own per-resource response interfaces
    # instead of using the generated ones (see e.g. frontend/src/api/
    # courses.ts's CourseBrowseResponse).
    results: list[Any]
