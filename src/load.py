"""
Output-writing logic for the PGA Tour pipeline.

write_to_files() persists an output DataFrame to disk as both a single flat
CSV and Parquet -- see its docstring for why both formats, and for the
temp-dir-then-rename dance the CSV side needs. write_to_postgres() is a
stub for the eventual Postgres JDBC write: the Postgres container and
connection details aren't set up yet, so it just documents the intended
signature and raises NotImplementedError for now.

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
    Writes `df` to a Postgres table via Spark's JDBC writer, using overwrite
    mode.

    NOT YET IMPLEMENTED -- the Postgres container and connection details
    aren't set up yet (this is being handled separately, alongside
    docker/init/schema.sql). Once that lands, this should look roughly
    like:

        df.write.jdbc(url=jdbc_url, table=table_name, mode="overwrite", properties=properties)

    `jdbc_url` is expected to look like
    "jdbc:postgresql://<host>:<port>/<database>", and `properties` should
    carry at least {"user": ..., "password": ..., "driver":
    "org.postgresql.Driver"}. The Postgres JDBC driver jar will also need to
    be on Spark's classpath (spark.jars / spark.jars.packages) for this to
    work -- it isn't bundled with the apache/spark image.

    Note "overwrite" mode here means DROP + recreate the target table on
    every run (matching the write_to_files() semantics above), not an
    upsert -- schema.sql's CREATE TABLE IF NOT EXISTS is only there for the
    very first run before any data exists.
    """
    raise NotImplementedError("Postgres JDBC write not yet configured")
