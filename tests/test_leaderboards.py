"""
Tests for GET /api/v1/leaderboards/season/{year} and
GET /api/v1/leaderboards/all-time.

All requests run against the seeded rows in tests/fixtures.py, never the
real dev database. See tests/fixtures.py's module docstring for why
Test Golfer One's two seasons share a stored sum_sg_total_rank of 1, and
why Test Golfer Two's single season has a populated sum_sg_total_rank
despite a NULL sum_sg_total.
"""


def test_season_leaderboard_excludes_null_value_row_despite_populated_rank(client):
    # 2020 has two rows: Test Golfer One (real sum_sg_total=20.0) and Test
    # Golfer Two (sum_sg_total NULL, but sum_sg_total_rank=99 -- the
    # ShotLink-gap-with-a-rank-anyway quirk from the leaderboard branch).
    # Golfer Two must not appear: filtering on the rank column alone
    # wouldn't catch this row, since its rank isn't null.
    response = client.get("/api/v1/leaderboards/season/2020", params={"category": "strokes_gained"})
    assert response.status_code == 200

    body = response.json()
    assert body["total"] == 1
    assert len(body["results"]) == 1
    entry = body["results"][0]
    assert entry["playerId"] == 90001
    assert entry["value"] == 20.0
    assert entry["rank"] == 1


def test_season_leaderboard_orders_by_stored_rank(client):
    # 2021 has two real rows: Test Golfer One (50.0, stored rank 1) and
    # Test Golfer Three (30.0, stored rank 2).
    response = client.get("/api/v1/leaderboards/season/2021", params={"category": "strokes_gained"})
    assert response.status_code == 200

    body = response.json()
    assert body["total"] == 2
    assert [row["playerId"] for row in body["results"]] == [90001, 90003]
    assert [row["value"] for row in body["results"]] == [50.0, 30.0]
    assert [row["rank"] for row in body["results"]] == [1, 2]


def test_season_leaderboard_empty_year_returns_empty_results_not_404(client):
    response = client.get("/api/v1/leaderboards/season/2099", params={"category": "strokes_gained"})
    assert response.status_code == 200
    assert response.json() == {"total": 0, "limit": 10, "offset": 0, "results": []}


def test_all_time_leaderboard_computes_fresh_cross_season_rank(client):
    # Qualifying rows (sum_sg_total NOT NULL), by value descending:
    #   Test Golfer One / 2021 -> 50.0
    #   Test Golfer Three / 2021 -> 30.0
    #   Test Golfer One / 2020 -> 20.0
    # Test Golfer One's two rows share a STORED sum_sg_total_rank of 1
    # (see tests/fixtures.py). If this endpoint mistakenly reused that
    # stored column instead of computing RANK() OVER (ORDER BY
    # sum_sg_total DESC) across all seasons at once, it would return
    # ranks [1, 2, 1] -- the same "rank 1" twice. The correct cross-season
    # computation must instead give three distinct ranks.
    response = client.get("/api/v1/leaderboards/all-time", params={"category": "strokes_gained"})
    assert response.status_code == 200

    body = response.json()
    assert body["total"] == 3  # excludes Test Golfer Two's null-value row
    results = body["results"]

    assert [row["rank"] for row in results] == [1, 2, 3]
    assert [row["value"] for row in results] == [50.0, 30.0, 20.0]
    assert [(row["playerId"], row["season"]) for row in results] == [
        (90001, 2021),
        (90003, 2021),
        (90001, 2020),
    ]
    # Genuinely cross-season: both 2020 and 2021 are represented, not just
    # whichever single season a buggy implementation might default to.
    assert {row["season"] for row in results} == {2020, 2021}


def test_leaderboard_rejects_invalid_category(client):
    response = client.get("/api/v1/leaderboards/season/2021", params={"category": "not_a_real_category"})
    assert response.status_code == 422


def test_leaderboard_requires_category(client):
    response = client.get("/api/v1/leaderboards/all-time")
    assert response.status_code == 422
