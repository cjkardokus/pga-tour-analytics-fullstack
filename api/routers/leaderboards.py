"""
Leaderboard endpoints -- ranks `player_season_stats` by one of the 16
metrics in CategoryEnum (see api/models/leaderboard.py), following the
same PaginatedResponse/raw-SQL conventions as courses.py and players.py.

IMPORTANT distinction between the two endpoints below: the stored
avg_sg_*_rank/sum_sg_*_rank columns are ranked WITHIN each season (a
PARTITION BY season window in the PySpark pipeline that built them -- see
src/transform.py) -- rank 1 appears once per season, not once overall.
That's exactly right for GET .../season/{year}, which filters to one
season anyway, but reusing those columns directly for GET .../all-time
would silently produce a "rank 1" six times over (once per season) rather
than one true cross-season rank 1. So all-time computes its own rank at
query time via RANK() OVER (ORDER BY <value column> DESC), with no
PARTITION BY, across every qualifying row regardless of season.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import PaginatedResponse
from api.models.leaderboard import CategoryEnum, LeaderboardEntry

router = APIRouter(prefix="/leaderboards", tags=["leaderboards"])

# Both endpoints select the same shape (LeaderboardEntry's fields, `value`
# aliased from whichever column the requested category maps to). Built
# per-request since the column names depend on `category`, but always
# from CategoryEnum.db_columns -- never from unvalidated user input -- so
# there's no injection surface despite the f-string interpolation below.
_ENTRY_COLUMNS = "player_id, player, season, tournaments_played"


@router.get("/season/{year}")
def get_season_leaderboard(
    year: int,
    category: CategoryEnum = Query(..., description="Which stat to rank players by."),
    limit: int = Query(10, ge=1, le=100, description="Max rows to return."),
    offset: int = Query(0, ge=0, description="Rows to skip."),
    db: Session = Depends(get_db),
) -> PaginatedResponse:
    """
    Ranks `year`'s players by `category`, using that category's stored
    per-season rank column (ascending -- rank 1 first). Rows are excluded
    if EITHER that rank column OR the underlying value column is null:
    the rank column alone isn't a reliable enough filter, because the
    `sum_sg_*` columns' stored rank is (as of this writing) populated even
    for the 203 rows with a ShotLink data gap in the value itself -- e.g.
    a real player-season with sum_sg_total NULL but sum_sg_total_rank=302.
    A handful of avg_sg_* rows exhibit the same mismatch. Filtering on
    both columns keeps every returned entry's `value` field genuinely
    displayable, regardless of which family's null-handling quirk applies.
    The 10-tournament qualifying threshold behind avg_sg_*_rank's own
    nulls is threshold logic already baked into the stored column by
    src/transform.py -- this endpoint doesn't reimplement it, just
    respects whatever's already null.

    A `year` with no rows at all (outside the dataset's 2017-2022 range,
    or simply a typo) returns `{"total": 0, "results": []}`, NOT a 404:
    "no results for this filter" is a normal, valid response for a
    collection endpoint -- unlike a single-resource lookup such as
    GET /api/v1/players/{player_id}, where a missing id has no other
    reasonable interpretation, an empty collection is exactly what an
    empty collection should return.
    """
    value_col, rank_col = category.db_columns
    where_clause = f"season = :year AND {rank_col} IS NOT NULL AND {value_col} IS NOT NULL"

    total = db.execute(
        text(f"SELECT count(*) FROM player_season_stats WHERE {where_clause}"),
        {"year": year},
    ).scalar_one()

    rows = (
        db.execute(
            text(
                f"SELECT {_ENTRY_COLUMNS}, {value_col} AS value, {rank_col} AS rank "
                f"FROM player_season_stats WHERE {where_clause} "
                f"ORDER BY {rank_col} ASC LIMIT :limit OFFSET :offset"
            ),
            {"year": year, "limit": limit, "offset": offset},
        )
        .mappings()
        .all()
    )
    return PaginatedResponse(
        total=total,
        limit=limit,
        offset=offset,
        results=[LeaderboardEntry.model_validate(dict(row)) for row in rows],
    )


@router.get("/all-time")
def get_all_time_leaderboard(
    category: CategoryEnum = Query(..., description="Which stat to rank players by."),
    limit: int = Query(10, ge=1, le=100, description="Max rows to return."),
    offset: int = Query(0, ge=0, description="Rows to skip."),
    db: Session = Depends(get_db),
) -> PaginatedResponse:
    """
    Ranks EVERY player-season in the table by `category`, regardless of
    season -- see this module's docstring for why that requires computing
    a fresh `RANK() OVER (ORDER BY <value column> DESC)` here rather than
    reusing the stored per-season rank column (which would repeat "rank 1"
    once per season instead of naming one true all-time best).

    Only the value column itself needs a null check here (the stored
    per-season rank column is irrelevant to this endpoint and never
    referenced) -- `WHERE <value column> IS NOT NULL` runs before the
    window function, so RANK() is computed only over rows that actually
    have a value to rank, with no gap in the resulting 1..N sequence.
    """
    value_col, _ = category.db_columns

    total = db.execute(
        text(f"SELECT count(*) FROM player_season_stats WHERE {value_col} IS NOT NULL")
    ).scalar_one()

    rows = (
        db.execute(
            text(
                f"SELECT {_ENTRY_COLUMNS}, {value_col} AS value, "
                f"RANK() OVER (ORDER BY {value_col} DESC) AS rank "
                f"FROM player_season_stats WHERE {value_col} IS NOT NULL "
                f"ORDER BY rank ASC LIMIT :limit OFFSET :offset"
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
        results=[LeaderboardEntry.model_validate(dict(row)) for row in rows],
    )
