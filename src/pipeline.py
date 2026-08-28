"""
Entry point for the PGA Tour PySpark pipeline.

Orchestrates extract -> transform -> load: reads the raw Kaggle export
(extract.extract_raw_data), cleans it and builds the two aggregated output
tables (transform.clean_raw_data / build_player_season_stats /
build_course_difficulty), then writes them out to both data/processed/
(load.write_to_files) and Postgres (load.write_to_postgres).

Run against the local Docker Spark cluster AND the Postgres container
(docker/docker-compose.yml must already be up), with a project-root `.env`
in place (see .env.example -- POSTGRES_DB/USER/PASSWORD must match
docker/.env, since that's what the Postgres container was actually
initialized with):

    python src/pipeline.py

The driver runs locally on the host and submits work to spark-master /
spark-worker over spark://localhost:7077. See PROJECT_DATA_DIR below for why
a single absolute path works for both the driver and the executors here.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from pyspark.sql import SparkSession

from extract import extract_raw_data
from load import write_to_files, write_to_postgres
from transform import build_course_difficulty, build_player_season_stats, clean_raw_data

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
# In client deploy mode, spark.read/write path resolution happens on the
# DRIVER's local filesystem (this process, running on the host), even though
# the actual task execution happens on the worker container(s). So the same
# absolute path has to resolve to the same file on both sides. The
# docker-compose setup achieves that by bind-mounting data/ into both
# containers at this exact host path, rather than remapping it to some
# container-only path -- see docker/docker-compose.yml. extract.py resolves
# this same PROJECT_ROOT independently for its own (raw-input) path needs;
# both resolve identically since every src/ module sits at the same depth
# under the project root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROJECT_DATA_DIR = PROJECT_ROOT / "data"

# Explicit path rather than a bare load_dotenv(): the latter searches upward
# from the current working directory, which would silently do the wrong
# thing (or nothing) if this script is ever run from somewhere other than
# the project root. This project-root .env is intentionally separate from
# docker/.env -- see .env.example for why, and note POSTGRES_DB/USER/
# PASSWORD have to match docker/.env's values exactly, since those are what
# the Postgres container was actually initialized with.
load_dotenv(PROJECT_ROOT / ".env")

# --------------------------------------------------------------------------
# Postgres JDBC driver
# --------------------------------------------------------------------------
# Postgres JDBC driver coordinate for Spark to pull via spark.jars.packages
# (Maven-style groupId:artifactId:version) -- lets Spark download (and
# cache) the driver jar itself rather than requiring a manually managed
# .jar on the classpath. 42.7.13 is the current stable release as of this
# writing.
POSTGRES_JDBC_PACKAGE = "org.postgresql:postgresql:42.7.13"


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------
def build_spark_session() -> SparkSession:
    return (
        SparkSession.builder.appName("pga-tour-transform")
        .master("spark://localhost:7077")
        .config("spark.jars.packages", POSTGRES_JDBC_PACKAGE)
        .getOrCreate()
    )


def build_postgres_jdbc_url() -> str:
    """
    Builds the JDBC URL Spark uses to reach Postgres. POSTGRES_HOST/PORT
    are expected to be "postgres"/"5432" -- the Docker-network service
    name, NOT "localhost:5432". This is the opposite of how
    PROJECT_DATA_DIR works above: a JDBC write opens its actual connections
    per-partition on the EXECUTORS (inside the spark-worker container),
    not the driver, so it needs a hostname reachable from *inside* the
    Docker network -- "localhost" there is the container's own loopback,
    not the host. See .env.example for details.
    """
    host = os.environ["POSTGRES_HOST"]
    port = os.environ["POSTGRES_PORT"]
    database = os.environ["POSTGRES_DB"]
    return f"jdbc:postgresql://{host}:{port}/{database}"


def build_postgres_properties() -> dict:
    """
    Builds the properties dict for load.write_to_postgres(). See that
    function's docstring for why "truncate": "true" is required here (in
    short: to preserve schema.sql's table structure -- PKs, constraints,
    indexes -- across every pipeline run, instead of Spark's default
    JDBC-overwrite behavior of dropping and recreating the table from a
    DataFrame-inferred schema).
    """
    return {
        "user": os.environ["POSTGRES_USER"],
        "password": os.environ["POSTGRES_PASSWORD"],
        "driver": "org.postgresql.Driver",
        "truncate": "true",
    }


def main() -> None:
    processed_dir = PROJECT_DATA_DIR / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    jdbc_url = build_postgres_jdbc_url()
    jdbc_properties = build_postgres_properties()

    spark = build_spark_session()
    try:
        raw_df = extract_raw_data(spark)
        print(f"\nRaw row count: {raw_df.count()}")
        raw_df.show(10, truncate=False)

        cleaned_df = clean_raw_data(raw_df)
        # Reused as the source for both output tables below (plus its own
        # checkpoint count/show), so cache it to avoid redoing the dedup +
        # filter chain three times over.
        cleaned_df.cache()
        print(f"\nCleaned row count: {cleaned_df.count()}")
        cleaned_df.show(10, truncate=False)

        player_season_stats = build_player_season_stats(cleaned_df)
        print(f"\nplayer_season_stats row count: {player_season_stats.count()}")
        player_season_stats.show(10, truncate=False)

        course_difficulty = build_course_difficulty(cleaned_df)
        print(f"\ncourse_difficulty row count: {course_difficulty.count()}")
        course_difficulty.show(10, truncate=False)

        write_to_files(player_season_stats, "player_season_stats", str(processed_dir))
        write_to_files(course_difficulty, "course_difficulty", str(processed_dir))
        print("\nWrote player_season_stats and course_difficulty to data/processed/ (csv + parquet).")

        # Table names match schema.sql: course_difficulty's output goes to
        # the "courses" table -- the name is intentionally different, see
        # docker/init/schema.sql.
        write_to_postgres(player_season_stats, "player_season_stats", jdbc_url, jdbc_properties)
        write_to_postgres(course_difficulty, "courses", jdbc_url, jdbc_properties)
        print("Wrote player_season_stats and courses to Postgres.")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
