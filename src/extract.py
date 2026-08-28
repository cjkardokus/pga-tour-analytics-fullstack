"""
Raw-data extraction for the PGA Tour pipeline.

Defines the explicit schema for the raw Kaggle CSV export and reads it,
returning the raw DataFrame (aside from dropping the header's junk
"Unnamed" columns -- see RAW_CSV_SCHEMA below for why those still have to
be declared).

See pipeline.py for the entry point that wires extract -> transform -> load
together.
"""

from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import DoubleType, IntegerType, StringType, StructField, StructType

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
# In client deploy mode, spark.read path resolution happens on the DRIVER's
# local filesystem (this process, running on the host), even though the
# actual task execution happens on the worker container(s). So the same
# absolute path has to resolve to the same file on both sides. The
# docker-compose setup achieves that by bind-mounting data/ into both
# containers at this exact host path, rather than remapping it to some
# container-only path -- see docker/docker-compose.yml. pipeline.py resolves
# this same PROJECT_ROOT independently for its own (processed-output) path
# needs; both resolve identically since every src/ module sits at the same
# depth under the project root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROJECT_DATA_DIR = PROJECT_ROOT / "data"

# --------------------------------------------------------------------------
# Schema
# --------------------------------------------------------------------------
# Explicit schema, no inferSchema -- avoids a slow extra scan of the file and
# avoids Spark silently guessing wrong types.
#
# NOTE: the raw CSV's header has three fully-empty junk columns (pandas
# labeled them Unnamed: 2/3/4, since they have no header text) sitting
# between `player` and `tournament name`. Spark's CSV reader maps an
# explicit schema to file columns *positionally*, so those three columns
# still have to be declared here to keep the rest of the schema aligned with
# the file -- they're dropped by name immediately after reading, in
# extract_raw_data() below, and never appear in any DataFrame after that.
RAW_CSV_SCHEMA = StructType(
    [
        StructField("Player_initial_last", StringType(), True),
        StructField("tournament id", IntegerType(), True),
        StructField("player id", IntegerType(), True),
        StructField("hole_par", IntegerType(), True),
        StructField("strokes", IntegerType(), True),
        StructField("hole_DKP", DoubleType(), True),
        StructField("hole_FDP", DoubleType(), True),
        StructField("hole_SDP", IntegerType(), True),
        StructField("streak_DKP", IntegerType(), True),
        StructField("streak_FDP", DoubleType(), True),
        StructField("streak_SDP", IntegerType(), True),
        StructField("n_rounds", IntegerType(), True),
        StructField("made_cut", IntegerType(), True),
        StructField("pos", DoubleType(), True),
        StructField("finish_DKP", IntegerType(), True),
        StructField("finish_FDP", IntegerType(), True),
        StructField("finish_SDP", IntegerType(), True),
        StructField("total_DKP", DoubleType(), True),
        StructField("total_FDP", DoubleType(), True),
        StructField("total_SDP", IntegerType(), True),
        StructField("player", StringType(), True),
        StructField("Unnamed: 2", StringType(), True),  # junk, dropped after read
        StructField("Unnamed: 3", StringType(), True),  # junk, dropped after read
        StructField("Unnamed: 4", StringType(), True),  # junk, dropped after read
        StructField("tournament name", StringType(), True),
        StructField("course", StringType(), True),
        StructField("date", StringType(), True),
        StructField("purse", DoubleType(), True),
        StructField("season", IntegerType(), True),
        StructField("no_cut", IntegerType(), True),
        StructField("Finish", StringType(), True),
        StructField("sg_putt", DoubleType(), True),
        StructField("sg_arg", DoubleType(), True),
        StructField("sg_app", DoubleType(), True),
        StructField("sg_ott", DoubleType(), True),
        StructField("sg_t2g", DoubleType(), True),
        StructField("sg_total", DoubleType(), True),
    ]
)


# --------------------------------------------------------------------------
# Extract
# --------------------------------------------------------------------------
def extract_raw_data(spark: SparkSession) -> DataFrame:
    """
    Reads the raw PGA Tour CSV using the explicit schema, returns the
    unmodified raw DataFrame (aside from dropping the header's junk
    "Unnamed" columns -- see RAW_CSV_SCHEMA above). No cleaning or
    aggregation happens here; see transform.py for that.
    """
    return (
        spark.read.option("header", True)
        .schema(RAW_CSV_SCHEMA)
        .csv(f"{PROJECT_DATA_DIR}/raw/pga_tour_raw.csv")
        .drop("Unnamed: 2", "Unnamed: 3", "Unnamed: 4")
    )
