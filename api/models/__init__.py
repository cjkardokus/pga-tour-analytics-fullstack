"""
Pydantic response models.

Empty placeholder aside from the shared pagination envelope below --
per-resource models (e.g. a CourseOut, PlayerSeasonStatsOut) get added here
on later branches, one module per resource, as their routes are built.
"""

from api.models.pagination import PaginatedResponse

__all__ = ["PaginatedResponse"]
