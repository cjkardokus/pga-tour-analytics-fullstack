
-- PGA Tour Analytics — PostgreSQL schema
-- Run once to initialize the database before the pipeline writes data.

CREATE TABLE IF NOT EXISTS courses (
    course_id       SERIAL PRIMARY KEY,
    course          TEXT NOT NULL UNIQUE,
    tournaments_hosted     INTEGER,
    avg_strokes_vs_par     DOUBLE PRECISION,
    avg_sg_total            DOUBLE PRECISION,
    avg_sg_putt              DOUBLE PRECISION,
    avg_sg_arg               DOUBLE PRECISION,
    avg_sg_app               DOUBLE PRECISION,
    avg_sg_ott                DOUBLE PRECISION,
    difficulty_rank          INTEGER,
    avg_strokes_vs_par_rank  INTEGER
);

CREATE TABLE IF NOT EXISTS player_season_stats (
    player_id       INTEGER NOT NULL,
    season          INTEGER NOT NULL,
    player          TEXT NOT NULL,
    tournaments_played     INTEGER,

    avg_sg_putt              DOUBLE PRECISION,
    avg_sg_arg                DOUBLE PRECISION,
    avg_sg_app                DOUBLE PRECISION,
    avg_sg_ott                DOUBLE PRECISION,
    avg_sg_t2g                DOUBLE PRECISION,
    avg_sg_total               DOUBLE PRECISION,

    sum_sg_putt               DOUBLE PRECISION,
    sum_sg_arg                 DOUBLE PRECISION,
    sum_sg_app                 DOUBLE PRECISION,
    sum_sg_ott                  DOUBLE PRECISION,
    sum_sg_t2g                  DOUBLE PRECISION,
    sum_sg_total                 DOUBLE PRECISION,

    wins                    INTEGER,
    top_5_finishes           INTEGER,
    top_10_finishes           INTEGER,
    cuts_made                  INTEGER,

    wins_rank                 INTEGER,
    top_5_finishes_rank        INTEGER,
    top_10_finishes_rank        INTEGER,
    cuts_made_rank                INTEGER,

    avg_sg_putt_rank          INTEGER,
    avg_sg_arg_rank            INTEGER,
    avg_sg_app_rank             INTEGER,
    avg_sg_ott_rank              INTEGER,
    avg_sg_t2g_rank               INTEGER,
    avg_sg_total_rank              INTEGER,

    sum_sg_putt_rank           INTEGER,
    sum_sg_arg_rank              INTEGER,
    sum_sg_app_rank               INTEGER,
    sum_sg_ott_rank                INTEGER,
    sum_sg_t2g_rank                 INTEGER,
    sum_sg_total_rank                INTEGER,

    sg_total_prev_season       DOUBLE PRECISION,
    sg_total_delta               DOUBLE PRECISION,

    PRIMARY KEY (player_id, season)
);

CREATE INDEX IF NOT EXISTS idx_player_season_stats_season ON player_season_stats (season);
CREATE INDEX IF NOT EXISTS idx_player_season_stats_player ON player_season_stats (player);