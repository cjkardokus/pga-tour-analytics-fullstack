"""
Players endpoints -- follows the exact pattern established by
api/routers/courses.py: browse/search on the list endpoint, raw
parameterized SQL (no ORM model classes, see api/database.py), and
HTTPException for not-found.

One structural difference from courses: `player_season_stats` has no
single row per player -- one row per (player_id, season), see
docker/init/schema.sql. So "get one player" splits into two endpoints
instead of one: a computed career aggregate (GET /{player_id}) and the
raw per-season rows behind it (GET /{player_id}/seasons).
"""

from typing import Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import PaginatedResponse
from api.models.player import PlayerCareerSummary, PlayerSeason, PlayerSummary

router = APIRouter(prefix="/players", tags=["players"])

# Explicit column list for the same reason as courses.py's _COURSE_COLUMNS:
# one place to update if schema.sql's player_season_stats columns change,
# and an at-a-glance match against PlayerSeason's fields.
_PLAYER_SEASON_COLUMNS = (
    "player_id, season, player, tournaments_played, wins, top_5_finishes, "
    "top_10_finishes, cuts_made, avg_sg_total, avg_sg_putt, avg_sg_arg, "
    "avg_sg_app, avg_sg_ott, avg_sg_t2g, sum_sg_total, sum_sg_putt, "
    "sum_sg_arg, sum_sg_app, sum_sg_ott, sum_sg_t2g, avg_sg_total_rank, "
    "avg_sg_putt_rank, avg_sg_arg_rank, avg_sg_app_rank, avg_sg_ott_rank, "
    "avg_sg_t2g_rank, sum_sg_total_rank, sum_sg_putt_rank, sum_sg_arg_rank, "
    "sum_sg_app_rank, sum_sg_ott_rank, sum_sg_t2g_rank, sg_total_prev_season, "
    "sg_total_delta"
)


@router.get("/")
def list_players(
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
        description="Case-insensitive partial match on player name. Switches the endpoint to search mode -- see below.",
    ),
    db: Session = Depends(get_db),
) -> Union[PaginatedResponse, list[PlayerSummary]]:
    """
    Same browse/search split as GET /api/v1/courses (see that endpoint's
    docstring for the full reasoning) -- search mode returns a bare,
    10-match-capped `list[PlayerSummary]` for a typeahead; browse mode
    returns the full player list as a `PaginatedResponse`, sorted by name
    ascending.

    Both modes query `DISTINCT player_id, player`: `player_season_stats`
    has one row per (player_id, season), so a plain SELECT would return
    Rory McIlroy once per season he has data for rather than once.

    `limit` is capped at 100 via `Query(le=100)`, rejecting an out-of-range
    value with a 422 rather than silently clamping it -- same reasoning as
    courses.py's list endpoint.
    """
    if search is not None:
        rows = (
            db.execute(
                text(
                    "SELECT DISTINCT player_id, player FROM player_season_stats "
                    "WHERE player ILIKE :pattern ORDER BY player LIMIT 10"
                ),
                {"pattern": f"%{search}%"},
            )
            .mappings()
            .all()
        )
        return [PlayerSummary.model_validate(dict(row)) for row in rows]

    total = db.execute(text("SELECT count(DISTINCT player_id) FROM player_season_stats")).scalar_one()
    rows = (
        db.execute(
            text(
                "SELECT DISTINCT player_id, player FROM player_season_stats "
                "ORDER BY player LIMIT :limit OFFSET :offset"
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
        results=[PlayerSummary.model_validate(dict(row)) for row in rows],
    )


@router.get("/{player_id}")
def get_player_career_summary(player_id: int, db: Session = Depends(get_db)) -> PlayerCareerSummary:
    """
    Career totals computed across all of `player_id`'s seasons -- not a
    stored row, so this is one aggregate query rather than a lookup.

    careerAverageStrokesGained is a WEIGHTED average --
    SUM(sum_sg_total) / SUM(tournaments_played) across the player's
    career -- not the mean of each season's avg_sg_total. An unweighted
    mean-of-means would reintroduce the exact small-sample distortion
    src/transform.py's difficulty ranking already had to correct for once
    (see its build_course_difficulty() docstring): a 3-tournament season
    would count exactly as much as a 25-tournament one, when the whole
    point of "career average" is that heavier seasons should count more.

    The SUM(tournaments_played) denominator is filtered to
    `sum_sg_total IS NOT NULL` seasons specifically -- not every season
    the player has a row for. Postgres's SUM() already silently skips NULL
    sum_sg_total values in the numerator (a season in the ShotLink data
    gap, see api/models/player.py), so leaving the denominator unfiltered
    would divide a partial numerator by a full denominator: e.g. Rory
    McIlroy's 2022 (tournaments_played=10, sum_sg_total NULL) would count
    those 10 tournaments against the average while contributing zero
    strokes-gained to it, silently dragging the number down. Filtering
    the denominator to the same qualifying seasons as the numerator keeps
    the two consistent; NULLIF guards the remaining edge case of a player
    whose every season falls in the gap (denominator, and hence the
    result, is NULL rather than a division error -- see
    PlayerCareerSummary's Optional typing for this field).

    careerStrokesGained (SUM(sum_sg_total), unfiltered) has no such
    ambiguity -- it's already a sum, not a rate, so there's nothing to
    weight.
    """
    row = db.execute(
        text(
            """
            SELECT
                player_id,
                max(player) AS player,
                count(DISTINCT season) AS seasons_played,
                sum(tournaments_played) AS tournaments_played,
                sum(wins) AS wins,
                sum(top_5_finishes) AS top_5_finishes,
                sum(top_10_finishes) AS top_10_finishes,
                sum(cuts_made) AS cuts_made,
                sum(sum_sg_total) AS career_strokes_gained,
                sum(sum_sg_total)
                    / nullif(sum(tournaments_played) FILTER (WHERE sum_sg_total IS NOT NULL), 0)
                    AS career_average_strokes_gained,
                min(season) AS first_season,
                max(season) AS last_season
            FROM player_season_stats
            WHERE player_id = :player_id
            GROUP BY player_id
            """
        ),
        {"player_id": player_id},
    ).mappings().first()

    if row is None:
        raise HTTPException(status_code=404, detail=f"Player with id {player_id} not found")
    return PlayerCareerSummary.model_validate(dict(row))


@router.get("/{player_id}/seasons")
def get_player_seasons(player_id: int, db: Session = Depends(get_db)) -> list[PlayerSeason]:
    """
    Every `player_season_stats` row for `player_id`, sorted season
    ascending. No PaginatedResponse envelope: a player has at most a
    handful of seasons in the current dataset (~6), so this isn't a
    "browse many things" endpoint the way GET /api/v1/players is.
    """
    rows = (
        db.execute(
            text(f"SELECT {_PLAYER_SEASON_COLUMNS} FROM player_season_stats WHERE player_id = :player_id ORDER BY season ASC"),
            {"player_id": player_id},
        )
        .mappings()
        .all()
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"Player with id {player_id} not found")
    return [PlayerSeason.model_validate(dict(row)) for row in rows]
