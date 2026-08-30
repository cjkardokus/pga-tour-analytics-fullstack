"""
Pydantic response models.

One module per resource (e.g. course.py's CourseResponse), added as each
resource's routes are built, plus the shared pagination envelope below.
"""

from api.models.pagination import PaginatedResponse

__all__ = ["PaginatedResponse"]
