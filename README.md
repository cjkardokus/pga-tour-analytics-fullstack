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

The PySpark pipeline runs against a local Docker Spark cluster and a
Postgres container -- see `docker/README.md` for full one-time setup
(including a required host-level step for the Postgres JDBC write) and
starting/stopping the cluster. In short, two `.env` files are needed before
first run:

- `docker/.env` (from `docker/.env.example`) -- configures the Docker
  Compose cluster itself (Spark bind-mount paths, Postgres credentials).
- `.env` at the project root (from `.env.example`) -- read by the pipeline
  itself to connect to Postgres. `POSTGRES_DB`/`USER`/`PASSWORD` here must
  match `docker/.env`'s values exactly.

Once the cluster is up and both `.env` files are in place:

```bash
python src/pipeline.py
```

`src/pipeline.py` is the entry point: it orchestrates the pipeline's
extract (`src/extract.py`) -> transform (`src/transform.py`) -> load
(`src/load.py`) stages in sequence, writing the aggregated output tables to
both `data/processed/` (CSV + Parquet) and Postgres (`player_season_stats`
and `courses`).
