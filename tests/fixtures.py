"""
Fixed, hand-verifiable seed data for the API test suite.

Every value here is deliberate, not arbitrary -- see the comments on each
row. Test modules import these constants directly (rather than
re-transcribing numbers into assertions) so the seed data and the
expected-value assertions can never drift apart.
"""

# --------------------------------------------------------------------------
# courses
# --------------------------------------------------------------------------
# Five rows: three complete, one ShotLink-gap row (all avg_sg_* and
# difficulty_rank NULL, mirroring the real 17-course gap seen in the dev
# data -- see api/models/course.py), plus one more to round out pagination.
# difficulty_rank values are deliberately non-sequential-by-insertion-order
# (9002=1, 9001=2, 9004=3, 9005=4, 9003=NULL) so a browse-mode test that
# asserts on ORDER BY difficulty_rank ASC NULLS LAST can't pass by
# accident just because it happens to match insertion order.
COURSES = [
    {
        "course_id": 9001,
        "course": "Whistling Test Links",
        "tournaments_hosted": 3,
        "avg_strokes_vs_par": 1.5,
        "avg_sg_total": 0.5,
        "avg_sg_putt": 0.1,
        "avg_sg_arg": 0.1,
        "avg_sg_app": 0.2,
        "avg_sg_ott": 0.1,
        "difficulty_rank": 2,
        "avg_strokes_vs_par_rank": 2,
    },
    {
        "course_id": 9002,
        "course": "Pebble Test Beach",
        "tournaments_hosted": 5,
        "avg_strokes_vs_par": 2.0,
        "avg_sg_total": 1.0,
        "avg_sg_putt": 0.3,
        "avg_sg_arg": 0.2,
        "avg_sg_app": 0.3,
        "avg_sg_ott": 0.2,
        "difficulty_rank": 1,
        "avg_strokes_vs_par_rank": 1,
    },
    {
        # The ShotLink-gap row: every avg_sg_* and difficulty_rank NULL,
        # exactly like the 17 real courses missing that data -- see
        # api/models/course.py's docstring. avg_strokes_vs_par and its
        # rank are still populated, since that fallback signal covers
        # every course regardless of ShotLink coverage.
        "course_id": 9003,
        "course": "Shadow Creek Test",
        "tournaments_hosted": 1,
        "avg_strokes_vs_par": -1.0,
        "avg_sg_total": None,
        "avg_sg_putt": None,
        "avg_sg_arg": None,
        "avg_sg_app": None,
        "avg_sg_ott": None,
        "difficulty_rank": None,
        "avg_strokes_vs_par_rank": 3,
    },
    {
        "course_id": 9004,
        "course": "Test Dunes Club",
        "tournaments_hosted": 2,
        "avg_strokes_vs_par": 0.5,
        "avg_sg_total": -0.2,
        "avg_sg_putt": -0.05,
        "avg_sg_arg": -0.05,
        "avg_sg_app": -0.05,
        "avg_sg_ott": -0.05,
        "difficulty_rank": 3,
        "avg_strokes_vs_par_rank": 4,
    },
    {
        "course_id": 9005,
        "course": "Test Meadows GC",
        "tournaments_hosted": 4,
        "avg_strokes_vs_par": 3.0,
        "avg_sg_total": -0.5,
        "avg_sg_putt": -0.1,
        "avg_sg_arg": -0.1,
        "avg_sg_app": -0.2,
        "avg_sg_ott": -0.1,
        "difficulty_rank": 4,
        "avg_strokes_vs_par_rank": 5,
    },
]

# difficulty_rank ASC NULLS LAST order, hand-derived from COURSES above --
# used by test_courses.py to assert browse-mode ordering.
COURSES_BY_DIFFICULTY = [9002, 9001, 9004, 9005, 9003]

# --------------------------------------------------------------------------
# player_season_stats
# --------------------------------------------------------------------------
# Three distinct players, four rows total:
#
# - "Test Golfer One" (90001): TWO seasons with no data gap, chosen so the
#   weighted vs. unweighted career average genuinely differ -- see
#   test_players.py for the hand-worked arithmetic. Its two rows also
#   share the SAME stored sum_sg_total_rank (1) on purpose: an all-time
#   leaderboard that (incorrectly) reused this stored per-season column
#   would show two rows tied at "rank 1"; the correct cross-season
#   RANK() OVER (ORDER BY sum_sg_total DESC) must not.
# - "Test Golfer Three" (90003): one season (2021), overlapping Golfer
#   One's second season, giving the 2021 season leaderboard and the
#   all-time leaderboard more than one real row to order.
# - "Test Golfer Two" (90002): one season (2020) reproducing the ShotLink-
#   gap quirk found on the leaderboard branch -- avg_sg_total/sum_sg_total
#   NULL, but sum_sg_total_rank populated anyway (99, an out-of-band value
#   distinct from every other seeded rank so it's unmistakable if it ever
#   leaks into a result). Exercises both PlayerSeason's nullability and
#   the leaderboard endpoints' "exclude on value, not just rank" filter.
PLAYER_SEASONS = [
    {
        "player_id": 90001,
        "season": 2020,
        "player": "Test Golfer One",
        "tournaments_played": 10,
        "wins": 1,
        "top_5_finishes": 2,
        "top_10_finishes": 3,
        "cuts_made": 8,
        "avg_sg_total": 2.0,
        "avg_sg_putt": 0.5,
        "avg_sg_arg": 0.3,
        "avg_sg_app": 0.6,
        "avg_sg_ott": 0.6,
        "avg_sg_t2g": 1.5,
        "sum_sg_total": 20.0,
        "sum_sg_putt": 5.0,
        "sum_sg_arg": 3.0,
        "sum_sg_app": 6.0,
        "sum_sg_ott": 6.0,
        "sum_sg_t2g": 15.0,
        "avg_sg_total_rank": 1,
        "avg_sg_putt_rank": 1,
        "avg_sg_arg_rank": 1,
        "avg_sg_app_rank": 1,
        "avg_sg_ott_rank": 1,
        "avg_sg_t2g_rank": 1,
        "sum_sg_total_rank": 1,  # deliberately == 2021's, see module docstring
        "sum_sg_putt_rank": 1,
        "sum_sg_arg_rank": 1,
        "sum_sg_app_rank": 1,
        "sum_sg_ott_rank": 1,
        "sum_sg_t2g_rank": 1,
        "sg_total_prev_season": None,  # first season on record
        "sg_total_delta": None,
    },
    {
        "player_id": 90001,
        "season": 2021,
        "player": "Test Golfer One",
        "tournaments_played": 20,
        "wins": 2,
        "top_5_finishes": 5,
        "top_10_finishes": 8,
        "cuts_made": 18,
        "avg_sg_total": 2.5,
        "avg_sg_putt": 0.5,
        "avg_sg_arg": 0.4,
        "avg_sg_app": 0.8,
        "avg_sg_ott": 0.8,
        "avg_sg_t2g": 2.0,
        "sum_sg_total": 50.0,
        "sum_sg_putt": 10.0,
        "sum_sg_arg": 8.0,
        "sum_sg_app": 16.0,
        "sum_sg_ott": 16.0,
        "sum_sg_t2g": 40.0,
        "avg_sg_total_rank": 1,
        "avg_sg_putt_rank": 1,
        "avg_sg_arg_rank": 1,
        "avg_sg_app_rank": 1,
        "avg_sg_ott_rank": 1,
        "avg_sg_t2g_rank": 1,
        "sum_sg_total_rank": 1,  # deliberately == 2020's, see module docstring
        "sum_sg_putt_rank": 1,
        "sum_sg_arg_rank": 1,
        "sum_sg_app_rank": 1,
        "sum_sg_ott_rank": 1,
        "sum_sg_t2g_rank": 1,
        "sg_total_prev_season": 2.0,  # 2020's avg_sg_total
        "sg_total_delta": 0.5,  # 2.5 - 2.0
    },
    {
        "player_id": 90003,
        "season": 2021,
        "player": "Test Golfer Three",
        "tournaments_played": 15,
        "wins": 0,
        "top_5_finishes": 1,
        "top_10_finishes": 4,
        "cuts_made": 12,
        "avg_sg_total": 2.0,
        "avg_sg_putt": 0.4,
        "avg_sg_arg": 4 / 15,
        "avg_sg_app": 10 / 15,
        "avg_sg_ott": 10 / 15,
        "avg_sg_t2g": 24 / 15,
        "sum_sg_total": 30.0,
        "sum_sg_putt": 6.0,
        "sum_sg_arg": 4.0,
        "sum_sg_app": 10.0,
        "sum_sg_ott": 10.0,
        "sum_sg_t2g": 24.0,
        "avg_sg_total_rank": 2,
        "avg_sg_putt_rank": 2,
        "avg_sg_arg_rank": 2,
        "avg_sg_app_rank": 2,
        "avg_sg_ott_rank": 2,
        "avg_sg_t2g_rank": 2,
        "sum_sg_total_rank": 2,
        "sum_sg_putt_rank": 2,
        "sum_sg_arg_rank": 2,
        "sum_sg_app_rank": 2,
        "sum_sg_ott_rank": 2,
        "sum_sg_t2g_rank": 2,
        "sg_total_prev_season": None,
        "sg_total_delta": None,
    },
    {
        # The ShotLink-gap row -- see module docstring.
        "player_id": 90002,
        "season": 2020,
        "player": "Test Golfer Two",
        "tournaments_played": 12,
        "wins": 0,
        "top_5_finishes": 1,
        "top_10_finishes": 2,
        "cuts_made": 9,
        "avg_sg_total": None,
        "avg_sg_putt": None,
        "avg_sg_arg": None,
        "avg_sg_app": None,
        "avg_sg_ott": None,
        "avg_sg_t2g": None,
        "sum_sg_total": None,
        "sum_sg_putt": None,
        "sum_sg_arg": None,
        "sum_sg_app": None,
        "sum_sg_ott": None,
        "sum_sg_t2g": None,
        "avg_sg_total_rank": None,
        "avg_sg_putt_rank": None,
        "avg_sg_arg_rank": None,
        "avg_sg_app_rank": None,
        "avg_sg_ott_rank": None,
        "avg_sg_t2g_rank": None,
        # Non-null despite every value above being NULL -- reproduces the
        # real anomaly documented in api/routers/leaderboards.py.
        "sum_sg_total_rank": 99,
        "sum_sg_putt_rank": 99,
        "sum_sg_arg_rank": 99,
        "sum_sg_app_rank": 99,
        "sum_sg_ott_rank": 99,
        "sum_sg_t2g_rank": 99,
        "sg_total_prev_season": None,
        "sg_total_delta": None,
    },
]

# Hand-worked expected values for Test Golfer One's career summary (see
# api/routers/players.py's weighted-average query) -- both of his seasons
# have real (non-NULL) sum_sg_total, so nothing gets filtered out of
# either sum below.
GOLFER_ONE_CAREER = {
    "seasons_played": 2,
    "tournaments_played": 30,  # 10 + 20
    "wins": 3,  # 1 + 2
    "top_5_finishes": 7,  # 2 + 5
    "top_10_finishes": 11,  # 3 + 8
    "cuts_made": 26,  # 8 + 18
    "career_strokes_gained": 70.0,  # 20.0 + 50.0
    "career_average_strokes_gained": 70.0 / 30,  # == 2.3333...; weighted by tournaments_played
    "first_season": 2020,
    "last_season": 2021,
}

# The WRONG, unweighted answer a mean-of-per-season-averages would give --
# test_players.py asserts the real endpoint does NOT return this.
GOLFER_ONE_UNWEIGHTED_AVERAGE = (2.0 + 2.5) / 2  # == 2.25
