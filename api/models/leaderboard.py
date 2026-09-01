"""
Category enum and response model for the leaderboard endpoints (see
api/routers/leaderboards.py).

`player_season_stats` (docker/init/schema.sql) carries a value column
(avg_sg_*, sum_sg_*, or one of the four counting stats) and a matching
stored rank column for each of the 16 metrics below. CategoryEnum is the
single place mapping the API-facing name a caller passes as
`?category=...` to that (value_column, rank_column) pair, so the router
never hardcodes column names inline.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class CategoryEnum(str, Enum):
    """
    A `str, Enum` (rather than a plain string with regex/`Literal`
    validation) so FastAPI renders this as an actual dropdown of the 16
    valid values in Swagger UI, and so an invalid value gets FastAPI's
    native 422 enum-validation error for free, instead of a custom check
    in the route.
    """

    average_strokes_gained = "average_strokes_gained"
    average_strokes_gained_putting = "average_strokes_gained_putting"
    average_strokes_gained_around_green = "average_strokes_gained_around_green"
    average_strokes_gained_approach = "average_strokes_gained_approach"
    average_strokes_gained_off_tee = "average_strokes_gained_off_tee"
    average_strokes_gained_tee_to_green = "average_strokes_gained_tee_to_green"
    strokes_gained = "strokes_gained"
    strokes_gained_putting = "strokes_gained_putting"
    strokes_gained_around_green = "strokes_gained_around_green"
    strokes_gained_approach = "strokes_gained_approach"
    strokes_gained_off_tee = "strokes_gained_off_tee"
    strokes_gained_tee_to_green = "strokes_gained_tee_to_green"
    wins = "wins"
    top_5_finishes = "top_5_finishes"
    top_10_finishes = "top_10_finishes"
    cuts_made = "cuts_made"

    @property
    def db_columns(self) -> tuple[str, str]:
        """(value_column, rank_column) in player_season_stats for this category."""
        return _CATEGORY_DB_COLUMNS[self]


_CATEGORY_DB_COLUMNS: dict[CategoryEnum, tuple[str, str]] = {
    CategoryEnum.average_strokes_gained: ("avg_sg_total", "avg_sg_total_rank"),
    CategoryEnum.average_strokes_gained_putting: ("avg_sg_putt", "avg_sg_putt_rank"),
    CategoryEnum.average_strokes_gained_around_green: ("avg_sg_arg", "avg_sg_arg_rank"),
    CategoryEnum.average_strokes_gained_approach: ("avg_sg_app", "avg_sg_app_rank"),
    CategoryEnum.average_strokes_gained_off_tee: ("avg_sg_ott", "avg_sg_ott_rank"),
    CategoryEnum.average_strokes_gained_tee_to_green: ("avg_sg_t2g", "avg_sg_t2g_rank"),
    CategoryEnum.strokes_gained: ("sum_sg_total", "sum_sg_total_rank"),
    CategoryEnum.strokes_gained_putting: ("sum_sg_putt", "sum_sg_putt_rank"),
    CategoryEnum.strokes_gained_around_green: ("sum_sg_arg", "sum_sg_arg_rank"),
    CategoryEnum.strokes_gained_approach: ("sum_sg_app", "sum_sg_app_rank"),
    CategoryEnum.strokes_gained_off_tee: ("sum_sg_ott", "sum_sg_ott_rank"),
    CategoryEnum.strokes_gained_tee_to_green: ("sum_sg_t2g", "sum_sg_t2g_rank"),
    # Counting stats -- see src/transform.py for why these are precomputed
    # per-season with no qualification threshold (same reasoning already
    # applied to sum_sg_*_rank above), and why there's deliberately no
    # all-time-specific stored column: the all-time endpoint below computes
    # its own fresh cross-season rank at query time instead.
    CategoryEnum.wins: ("wins", "wins_rank"),
    CategoryEnum.top_5_finishes: ("top_5_finishes", "top_5_finishes_rank"),
    CategoryEnum.top_10_finishes: ("top_10_finishes", "top_10_finishes_rank"),
    CategoryEnum.cuts_made: ("cuts_made", "cuts_made_rank"),
}


class LeaderboardEntry(BaseModel):
    """
    One row of a leaderboard, for either GET /api/v1/leaderboards/season/{year}
    or GET /api/v1/leaderboards/all-time.

    `season` is included on both endpoints, not just the season one:
    every leaderboard entry -- all-time included -- is still one specific
    player-season's performance; all-time just ranks those rows across
    every season at once rather than filtering to one first. Dropping
    `season` from the all-time shape would actually lose information a
    caller needs: the same player can appear more than once (once per
    qualifying season), and without `season` two of that player's entries
    would be indistinguishable.
    """

    model_config = ConfigDict(populate_by_name=True)

    player_id: int = Field(alias="playerId")
    player: str
    season: int
    tournaments_played: int = Field(alias="tournamentsPlayed")
    value: float
    rank: int


class AvailableSeasonsResponse(BaseModel):
    """
    Response shape for GET /api/v1/leaderboards/seasons -- the distinct
    list of seasons with data in `player_season_stats`, sorted ascending.

    A plain wrapped list, not a `PaginatedResponse`: this will only ever
    return a handful of years (one per season the pipeline has ingested),
    nowhere near needing pagination.
    """

    seasons: list[int]
