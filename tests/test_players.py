"""
Tests for GET /api/v1/players, GET /api/v1/players/{player_id}, and
GET /api/v1/players/{player_id}/seasons.

All requests run against the seeded rows in tests/fixtures.py, never the
real dev database.
"""

import pytest

from tests.fixtures import GOLFER_ONE_CAREER, GOLFER_ONE_UNWEIGHTED_AVERAGE


def test_browse_players_returns_distinct_players_sorted_by_name(client):
    response = client.get("/api/v1/players/")
    assert response.status_code == 200

    body = response.json()
    # 3 distinct players seeded, even though Test Golfer One has 2 rows
    # (one per season) in player_season_stats -- a plain (non-DISTINCT)
    # query would over-count this to 4.
    assert body["total"] == 3
    names = [row["player"] for row in body["results"]]
    assert names == ["Test Golfer One", "Test Golfer Three", "Test Golfer Two"]


def test_search_players_returns_one_result_per_player_not_per_season(client):
    response = client.get("/api/v1/players/", params={"search": "One"})
    assert response.status_code == 200

    body = response.json()
    # Bare list (search mode), and exactly one entry despite Test Golfer
    # One having two player_season_stats rows.
    assert isinstance(body, list)
    assert len(body) == 1
    assert body[0]["player"] == "Test Golfer One"
    assert body[0]["playerId"] == 90001


def test_player_career_summary_uses_weighted_average(client):
    response = client.get("/api/v1/players/90001")
    assert response.status_code == 200

    body = response.json()
    assert body["seasonsPlayed"] == GOLFER_ONE_CAREER["seasons_played"]
    assert body["tournamentsPlayed"] == GOLFER_ONE_CAREER["tournaments_played"]
    assert body["wins"] == GOLFER_ONE_CAREER["wins"]
    assert body["top5Finishes"] == GOLFER_ONE_CAREER["top_5_finishes"]
    assert body["top10Finishes"] == GOLFER_ONE_CAREER["top_10_finishes"]
    assert body["cutsMade"] == GOLFER_ONE_CAREER["cuts_made"]
    assert body["firstSeason"] == GOLFER_ONE_CAREER["first_season"]
    assert body["lastSeason"] == GOLFER_ONE_CAREER["last_season"]
    assert body["careerStrokesGained"] == pytest.approx(GOLFER_ONE_CAREER["career_strokes_gained"])

    # The actual point of this test: SUM(sum_sg_total)/SUM(tournaments_played)
    # == 70.0 / 30 == 2.3333..., weighted toward the 20-tournament 2021
    # season -- NOT the unweighted mean of the two seasons' avg_sg_total
    # (2.0 and 2.5), which would be 2.25.
    career_average = body["careerAverageStrokesGained"]
    assert career_average == pytest.approx(GOLFER_ONE_CAREER["career_average_strokes_gained"])
    assert career_average != pytest.approx(GOLFER_ONE_UNWEIGHTED_AVERAGE)


def test_player_career_summary_not_found(client):
    response = client.get("/api/v1/players/999999999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Player with id 999999999 not found"}


def test_player_seasons_returns_all_seasons_ascending(client):
    response = client.get("/api/v1/players/90001/seasons")
    assert response.status_code == 200

    body = response.json()
    assert isinstance(body, list)  # no pagination envelope
    assert [row["season"] for row in body] == [2020, 2021]

    first_season, second_season = body
    assert first_season["tournamentsPlayed"] == 10
    assert first_season["averageStrokesGainedPreviousSeason"] is None  # first season on record
    assert first_season["averageStrokesGainedDelta"] is None

    assert second_season["tournamentsPlayed"] == 20
    assert second_season["averageStrokesGainedPreviousSeason"] == pytest.approx(2.0)
    assert second_season["averageStrokesGainedDelta"] == pytest.approx(0.5)


def test_player_seasons_not_found(client):
    response = client.get("/api/v1/players/999999999/seasons")
    assert response.status_code == 404
    assert response.json() == {"detail": "Player with id 999999999 not found"}
