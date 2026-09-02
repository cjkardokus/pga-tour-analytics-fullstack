"""
Courses endpoints -- the first business-logic routes on the API, and the
template api/routers/players.py and leaderboards.py both follow: response
fields renamed away from raw DB columns (see
api/models/course.py), a PaginatedResponse envelope for browsing, a
lightweight search mode, and HTTPException for not-found.

Queries here are raw parameterized SQL via `db.execute(text(...), params)`,
not ORM query-building -- consistent with api/database.py's docstring:
this layer deliberately has no SQLAlchemy ORM model classes, so there's no
mapped `Course` class to query against. `courses` is a small, already-
aggregated table (81 rows as of this writing, see
src/transform.py's build_course_difficulty()) with a handful of read
patterns, which raw SQL expresses directly without adding an ORM layer
that isn't earning its keep yet.
"""

from typing import Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import PaginatedResponse
from api.models.course import CourseResponse

router = APIRouter(prefix="/courses", tags=["courses"])

# Selected explicitly (rather than `SELECT *`) so this list stays the one
# place that has to change if schema.sql's courses columns ever do, and so
# it's obvious at a glance that it lines up with CourseResponse's fields.
_COURSE_COLUMNS = (
    "course_id, course, tournaments_hosted, avg_strokes_vs_par, avg_sg_total, "
    "avg_sg_putt, avg_sg_arg, avg_sg_app, avg_sg_ott, difficulty_rank, "
    "avg_strokes_vs_par_rank"
)


@router.get("/")
def list_courses(
    limit: int = Query(
        20,
        ge=1,
        le=100,
        description="Max rows to return in browse mode. Ignored in search mode (fixed at 10 -- see `search`).",
    ),
    offset: int = Query(0, ge=0, description="Rows to skip in browse mode. Ignored in search mode."),
    search: Optional[str] = Query(
        None,
        min_length=1,
        description="Case-insensitive partial match on course name. Switches the endpoint to search mode -- see below.",
    ),
    db: Session = Depends(get_db),
) -> Union[PaginatedResponse, list[CourseResponse]]:
    """
    Two distinct modes behind one endpoint, chosen by whether `search` is
    given:

    - **search mode** (`search` present): powers a type-to-search-and-
      select UI control (an autocomplete/typeahead), not a browsable list
      -- a caller there wants "the handful of courses matching what's
      typed so far", not a page out of the full table. Returns a bare
      `list[CourseResponse]`, capped at 10 matches, with no
      PaginatedResponse envelope: `total`/`limit`/`offset` describe a
      paginated browse, which this isn't, so they'd only be noise here.
      `limit`/`offset` are ignored in this mode.
    - **browse mode** (no `search`): the standard paginated list, wrapped
      in `PaginatedResponse`. Sorted by difficulty_rank ascending with
      NULLs last: the 17 courses with a ShotLink data gap have no
      difficulty_rank at all (see docker/init/schema.sql and
      src/transform.py's build_course_difficulty(), which computes this
      same column with `F.asc_nulls_last` for the identical reason --
      Postgres's plain `ASC` would otherwise sort NULLs *first*, putting
      "no rank" courses ahead of "hardest" instead of after "easiest").

    `limit` is capped at 100 via FastAPI's `Query(le=100)`, which rejects
    an out-of-range value with a 422 rather than silently clamping it --
    a client asking for 200 rows and quietly getting 100 back with no
    indication would be a harder bug to notice than a validation error.
    """
    if search is not None:
        rows = (
            db.execute(
                text(f"SELECT {_COURSE_COLUMNS} FROM courses WHERE course ILIKE :pattern ORDER BY course LIMIT 10"),
                {"pattern": f"%{search}%"},
            )
            .mappings()
            .all()
        )
        return [CourseResponse.model_validate(dict(row)) for row in rows]

    total = db.execute(text("SELECT count(*) FROM courses")).scalar_one()
    rows = (
        db.execute(
            text(
                f"SELECT {_COURSE_COLUMNS} FROM courses "
                "ORDER BY difficulty_rank ASC NULLS LAST "
                "LIMIT :limit OFFSET :offset"
            ),
            {"limit": limit, "offset": offset},
        )
        .mappings()
        .all()
    )
    return PaginatedResponse(
        total=total,
        limit=limit,
        offset=offset,
        results=[CourseResponse.model_validate(dict(row)) for row in rows],
    )


@router.get("/{course_id}")
def get_course(course_id: int, db: Session = Depends(get_db)) -> CourseResponse:
    row = (
        db.execute(
            text(f"SELECT {_COURSE_COLUMNS} FROM courses WHERE course_id = :course_id"),
            {"course_id": course_id},
        )
        .mappings()
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail=f"Course with id {course_id} not found")
    return CourseResponse.model_validate(dict(row))
