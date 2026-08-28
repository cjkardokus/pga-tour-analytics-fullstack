"""
Output-writing logic for the PGA Tour pipeline.

write_to_files() persists an output DataFrame to disk as both a single flat
CSV and Parquet -- see its docstring for why both formats, and for the
temp-dir-then-rename dance the CSV side needs. write_to_postgres() writes a
DataFrame to a Postgres table via Spark's JDBC writer -- see its docstring
for why "truncate": "true" is required in `properties` to avoid clobbering
docker/init/schema.sql's table structure on every run.

See pipeline.py for the entry point that wires extract -> transform -> load
together.
"""

import shutil
from pathlib import Path

from pyspark.sql import DataFrame


def write_to_files(df: DataFrame, name: str, output_dir: str) -> None:
    """
    Writes `df` to `output_dir` as both Parquet and a single flat CSV,
    named `{name}.parquet` / `{name}.csv`.

    Parquet is the "proper" output here -- compressed, typed, splittable
    columnar storage, and what a real downstream Spark/warehouse job would
    consume. CSV is written alongside it purely for convenience (a quick
    open in Excel/Power BI).

    Spark's CSV writer always produces a *directory* of part-files, even
    forced to one partition via coalesce(1) -- there's no writer option that
    produces a bare .csv file directly. So we write CSV to a throwaway
    directory and then promote the single part-file to a flat filename
    ourselves, cleaning up Spark's directory litter (_SUCCESS, checksums,
    etc.) afterward. coalesce(1) is safe here specifically because these are
    small, already-aggregated tables -- doing this on the raw, row-level
    dataset would kill parallelism.
    """
    output_path = Path(output_dir)
    df.write.mode("overwrite").parquet(f"{output_path}/{name}.parquet")

    tmp_name = f"_{name}_csv_tmp"
    df.coalesce(1).write.mode("overwrite").option("header", True).csv(f"{output_path}/{tmp_name}")

    # The plain-Python cleanup below (promoting Spark's single part-file to
    # a flat filename) runs in this same process, on this same path -- no
    # separate host/container path to reconcile.
    tmp_dir = output_path / tmp_name
    final_path = output_path / f"{name}.csv"

    part_file = next(tmp_dir.glob("part-*.csv"))
    if final_path.exists():
        final_path.unlink()
    part_file.rename(final_path)
    shutil.rmtree(tmp_dir)


def write_to_postgres(df: DataFrame, table_name: str, jdbc_url: str, properties: dict) -> None:
    """
    Writes `df` to a Postgres table via Spark's JDBC writer.

    `jdbc_url` looks like "jdbc:postgresql://<host>:<port>/<database>"; see
    pipeline.py for how it's built from POSTGRES_HOST/PORT/DB env vars.
    `properties` must carry at least {"user": ..., "password": ...,
    "driver": "org.postgresql.Driver"} -- see pipeline.py for how it's
    built from POSTGRES_USER/PASSWORD env vars. The driver class itself
    doesn't need to be manually installed: pipeline.py's build_spark_session()
    configures spark.jars.packages with the Postgres JDBC driver coordinate,
    so Spark downloads (and caches) the jar automatically.

    properties carrying "truncate": "true" alongside mode="overwrite" is
    deliberate, not incidental: Spark's JDBC writer's mode="overwrite" DROPS
    and RECREATES the target table by default, using a schema inferred
    purely from the DataFrame -- which would destroy schema.sql's actual table
    definition (course_id SERIAL PRIMARY KEY + course UNIQUE for courses;
    the composite (player_id, season) PRIMARY KEY for player_season_stats;
    both tables' indexes) on the very first pipeline run after
    `docker compose up` creates them. Concretely, `courses` would lose its
    course_id surrogate key entirely, since the course_difficulty DataFrame
    doesn't have a course_id column to infer one from -- the whole point of
    a DB-generated surrogate key is that Spark never has to know about it.
    Passing properties={"truncate": "true", ...} instead makes Spark issue
    TRUNCATE + INSERT when mode="overwrite" and the table already exists,
    which clears all rows but leaves schema.sql's table structure (columns,
    types, constraints, indexes) completely intact across every run.
    truncate depends on the table already existing with the right
    structure, which is exactly what schema.sql's CREATE TABLE IF NOT
    EXISTS guarantees on container startup -- see docker/init/schema.sql
    and docker/README.md.
    """
    df.write.jdbc(url=jdbc_url, table=table_name, mode="overwrite", properties=properties)
