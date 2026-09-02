"""
Response models for `player_season_stats` (see docker/init/schema.sql).

Same renaming convention as api/models/course.py: DB columns map to
camelCase fields via `alias`, with `populate_by_name=True` so each model
can still be built from a DB row's snake_case attributes.

Nullability note: the DB columns nullable in practice are wider than
api/routers/players.py's task description called out. It named the
avg_sg_*_rank fields (null below the tournaments_played qualifying
threshold used by src/transform.py's ranking window) and
sg_total_prev_season/sg_total_delta (null for a player's first season,
with no prior season to compare against). Checked against the actual
table, though: avg_sg_total/_putt/_arg/_app/_ott/_t2g and their sum_sg_*
counterparts are ALSO null for 203 of 2184 rows -- the same kind of
ShotLink data gap already documented for `courses` (see
api/models/course.py), not a threshold effect (e.g. Rory McIlroy's 2022
season, tournaments_played=10, still has null sum_sg_total). Those had to
be marked Optional too, or model_validate() would raise on the first row
with a real gap. sum_sg_*_rank fields, by contrast, are never null in the
table (confirmed: 0 nulls across all 2184 rows, even for seasons where the
underlying sum_sg_* value itself is null) -- left non-Optional to match.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PlayerSummary(BaseModel):
    """List/search-mode shape -- just enough to identify a player and let
    a caller drill into GET /api/v1/players/{player_id}. There's no
    single "player" row to return more of: every DB row is one
    player-season, so anything beyond id/name is necessarily an aggregate
    (see PlayerCareerSummary) or per-season (see PlayerSeason), not a flat
    field on this model.
    """

    model_config = ConfigDict(populate_by_name=True)

    player_id: int = Field(alias="playerId")
    player: str


class PlayerSeason(BaseModel):
    """One row of `player_season_stats`, in full -- returned by
    GET /api/v1/players/{player_id}/seasons.
    """

    model_config = ConfigDict(populate_by_name=True)

    player_id: int = Field(alias="playerId")
    season: int
    player: str

    tournaments_played: int = Field(alias="tournamentsPlayed")
    wins: int
    top_5_finishes: int = Field(alias="top5Finishes")
    top_10_finishes: int = Field(alias="top10Finishes")
    cuts_made: int = Field(alias="cutsMade")

    # See the module docstring: null for the same ShotLink-gap seasons as
    # `courses`' avg_sg_* fields, not just below some tournament-count
    # threshold.
    avg_sg_total: Optional[float] = Field(alias="averageStrokesGained")
    avg_sg_putt: Optional[float] = Field(alias="averageStrokesGainedPutting")
    avg_sg_arg: Optional[float] = Field(alias="averageStrokesGainedAroundGreen")
    avg_sg_app: Optional[float] = Field(alias="averageStrokesGainedApproach")
    avg_sg_ott: Optional[float] = Field(alias="averageStrokesGainedOffTee")
    avg_sg_t2g: Optional[float] = Field(alias="averageStrokesGainedTeeToGreen")

    sum_sg_total: Optional[float] = Field(alias="strokesGained")
    sum_sg_putt: Optional[float] = Field(alias="strokesGainedPutting")
    sum_sg_arg: Optional[float] = Field(alias="strokesGainedAroundGreen")
    sum_sg_app: Optional[float] = Field(alias="strokesGainedApproach")
    sum_sg_ott: Optional[float] = Field(alias="strokesGainedOffTee")
    sum_sg_t2g: Optional[float] = Field(alias="strokesGainedTeeToGreen")

    # Null below the qualifying tournaments_played threshold applied by
    # src/transform.py's ranking window (and, transitively, whenever the
    # underlying avg_sg_* value above is itself null).
    avg_sg_total_rank: Optional[int] = Field(alias="averageStrokesGainedRank")
    avg_sg_putt_rank: Optional[int] = Field(alias="averageStrokesGainedPuttingRank")
    avg_sg_arg_rank: Optional[int] = Field(alias="averageStrokesGainedAroundGreenRank")
    avg_sg_app_rank: Optional[int] = Field(alias="averageStrokesGainedApproachRank")
    avg_sg_ott_rank: Optional[int] = Field(alias="averageStrokesGainedOffTeeRank")
    avg_sg_t2g_rank: Optional[int] = Field(alias="averageStrokesGainedTeeToGreenRank")

    # sum_sg_*_rank fields are never null in the table -- see module
    # docstring -- so these stay plain `int`.
    sum_sg_total_rank: int = Field(alias="strokesGainedRank")
    sum_sg_putt_rank: int = Field(alias="strokesGainedPuttingRank")
    sum_sg_arg_rank: int = Field(alias="strokesGainedAroundGreenRank")
    sum_sg_app_rank: int = Field(alias="strokesGainedApproachRank")
    sum_sg_ott_rank: int = Field(alias="strokesGainedOffTeeRank")
    sum_sg_t2g_rank: int = Field(alias="strokesGainedTeeToGreenRank")

    sg_total_prev_season: Optional[float] = Field(alias="averageStrokesGainedPreviousSeason")
    sg_total_delta: Optional[float] = Field(alias="averageStrokesGainedDelta")


class PlayerCareerSummary(BaseModel):
    """Computed via aggregate SQL across all of a player's seasons (see
    api/routers/players.py's career query) -- not a raw DB row, so unlike
    CourseResponse/PlayerSeason there's no 1:1 column to alias from.
    """

    model_config = ConfigDict(populate_by_name=True)

    player_id: int = Field(alias="playerId")
    player: str

    seasons_played: int = Field(alias="seasonsPlayed")
    tournaments_played: int = Field(alias="tournamentsPlayed")
    wins: int
    top_5_finishes: int = Field(alias="top5Finishes")
    top_10_finishes: int = Field(alias="top10Finishes")
    cuts_made: int = Field(alias="cutsMade")

    # Optional, not because of a threshold, but because it's arithmetically
    # undefined for the (rare) player whose every season falls in the
    # ShotLink data gap -- see api/routers/players.py's career query for
    # how the weighting itself works and why it has to be Optional here.
    career_average_strokes_gained: Optional[float] = Field(alias="careerAverageStrokesGained")
    career_strokes_gained: Optional[float] = Field(alias="careerStrokesGained")

    first_season: int = Field(alias="firstSeason")
    last_season: int = Field(alias="lastSeason")
