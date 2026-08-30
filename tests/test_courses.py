"""
Tests for GET /api/v1/courses and GET /api/v1/courses/{course_id}.

All requests run against the seeded rows in tests/fixtures.py (via the
`client` fixture in tests/conftest.py), never the real dev database.
"""

from tests.fixtures import COURSES_BY_DIFFICULTY


def test_browse_courses_returns_paginated_envelope_ordered_by_difficulty(client):
    response = client.get("/api/v1/courses/")
    assert response.status_code == 200

    body = response.json()
    # Envelope shape: total/limit/offset/results, not a bare list.
    assert body["total"] == len(COURSES_BY_DIFFICULTY)
    assert body["limit"] == 20
    assert body["offset"] == 0

    # difficulty_rank ASC NULLS LAST: the one seeded course with no
    # difficulty_rank (course_id 9003) has to come out last, not first
    # (Postgres's plain ASC would otherwise sort NULLs first).
    returned_ids = [row["courseId"] for row in body["results"]]
    assert returned_ids == COURSES_BY_DIFFICULTY

    null_difficulty_course = body["results"][-1]
    assert null_difficulty_course["courseId"] == 9003
    assert null_difficulty_course["difficultyRank"] is None
    assert null_difficulty_course["averageStrokesGained"] is None
    # Non-SG fields stay populated even on the ShotLink-gap row.
    assert null_difficulty_course["averageStrokesVsPar"] == -1.0


def test_search_courses_returns_bare_list_not_envelope(client):
    response = client.get("/api/v1/courses/", params={"search": "Pebble"})
    assert response.status_code == 200

    body = response.json()
    # Search mode: a plain list, no total/limit/offset wrapper.
    assert isinstance(body, list)
    assert len(body) == 1
    assert body[0]["course"] == "Pebble Test Beach"
    assert body[0]["courseId"] == 9002


def test_get_course_by_id(client):
    response = client.get("/api/v1/courses/9002")
    assert response.status_code == 200

    body = response.json()
    assert body["courseId"] == 9002
    assert body["course"] == "Pebble Test Beach"
    assert body["difficultyRank"] == 1
    assert body["averageStrokesGained"] == 1.0


def test_get_course_by_id_not_found(client):
    response = client.get("/api/v1/courses/999999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Course with id 999999 not found"}


def test_browse_courses_rejects_over_limit(client):
    response = client.get("/api/v1/courses/", params={"limit": 200})
    assert response.status_code == 422
