# pga-tour-analytics-fullstack
A full-stack PGA Tour analytics application: PySpark data pipeline → PostgreSQL → FastAPI → React.

## Status
Early development — building on the validated PySpark pipeline from [pga-tour-pyspark-pipeline](https://github.com/cjkardokus/pga-tour-pyspark-pipeline).

## Planned Stack
- **PySpark** — data transformation (reused from the prior project)
- **PostgreSQL** — persistent data store
- **FastAPI** — REST API layer
- **React** — front-end

## Setup

The PySpark pipeline runs against a local Docker Spark cluster -- see
`docker/README.md` for one-time setup and starting/stopping the cluster.
Once it's up:

```bash
python src/pipeline.py
```

`src/pipeline.py` is the entry point: it orchestrates the pipeline's
extract (`src/extract.py`) -> transform (`src/transform.py`) -> load
(`src/load.py`) stages in sequence and writes the aggregated output tables
to `data/processed/` (CSV + Parquet).
