"""
Response model for the `courses` table (see docker/init/schema.sql).

Field names are deliberately renamed from the raw DB columns to camelCase
via each field's `alias`, decoupling the API's public shape from Postgres's
column names -- so a future column rename/refactor on the DB side doesn't
have to be a breaking API change, and vice versa. `populate_by_name=True`
lets the model still be constructed from a DB row's snake_case attributes
(as `CourseResponse.model_validate(row, from_attributes=True)` does in
api/routers/courses.py) while serializing under the camelCase aliases.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CourseResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    course_id: int = Field(alias="courseId")
    course: str

    tournaments_hosted: int = Field(alias="tournamentsHosted")

    # avg_strokes_vs_par/avg_strokes_vs_par_rank are populated for every row
    # (see courses.py's query comment); difficulty_rank and the avg_sg_*
    # fields below are NULL for the 17 courses with a ShotLink data gap --
    # left Optional rather than coerced to a placeholder value.
    avg_strokes_vs_par: float = Field(alias="averageStrokesVsPar")
    avg_strokes_vs_par_rank: int = Field(alias="averageStrokesVsParRank")

    avg_sg_total: Optional[float] = Field(alias="averageStrokesGained")
    avg_sg_putt: Optional[float] = Field(alias="averageStrokesGainedPutting")
    avg_sg_arg: Optional[float] = Field(alias="averageStrokesGainedAroundGreen")
    avg_sg_app: Optional[float] = Field(alias="averageStrokesGainedApproach")
    avg_sg_ott: Optional[float] = Field(alias="averageStrokesGainedOffTee")

    difficulty_rank: Optional[int] = Field(alias="difficultyRank")
