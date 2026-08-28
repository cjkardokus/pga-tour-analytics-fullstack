"""
Entry point for the PGA Tour PySpark pipeline.

Orchestrates extract -> transform -> load: reads the raw Kaggle export
(extract.extract_raw_data), cleans it and builds the two aggregated output
tables (transform.clean_raw_data / build_player_season_stats /
build_course_difficulty), then writes them out (load.write_to_files -- and,
eventually, load.write_to_postgres once that's implemented).

Run against the local Docker Spark cluster (docker/docker-compose.yml must
already be up):

    python src/pipeline.py

The driver runs locally on the host and submits work to spark-master /
spark-worker over spark://localhost:7077. See PROJECT_DATA_DIR below for why
a single absolute path works for both the driver and the executors here.
"""

from pathlib import Path

from pyspark.sql import SparkSession

from extract import extract_raw_data
from load import write_to_files
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


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------
def build_spark_session() -> SparkSession:
    return SparkSession.builder.appName("pga-tour-transform").master("spark://localhost:7077").getOrCreate()


def main() -> None:
    processed_dir = PROJECT_DATA_DIR / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

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
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
