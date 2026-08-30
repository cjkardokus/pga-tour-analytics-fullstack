# pga-tour-analytics-fullstack
A full-stack PGA Tour analytics application: PySpark data pipeline → PostgreSQL → FastAPI → React.

## Status
The PySpark pipeline and its Postgres store are complete and working
end-to-end. The FastAPI layer's data-facing surface is now complete too
-- `courses`, `players`, and `leaderboards` cover everything in the
current schema -- though the API as a whole still has no auth, tests, or
deployment story yet. The React front-end hasn't been started.

## Stack
- **PySpark** — data transformation (reused from the prior
  [pga-tour-pyspark-pipeline](https://github.com/cjkardokus/pga-tour-pyspark-pipeline)
  project) ✅ implemented — `src/extract.py` → `transform.py` → `load.py`,
  orchestrated by `src/pipeline.py`
- **PostgreSQL** — persistent data store ✅ implemented — schema in
  `docker/init/schema.sql` (`courses`, `player_season_stats`), run via
  Docker Compose alongside the Spark cluster, written to by the pipeline's
  JDBC load step
- **FastAPI** — REST API layer ✅ data-facing endpoints implemented —
  foundation (app, DB session handling, CORS, `/api/v1` versioning) plus
  three resources covering the full schema: `courses`, `players`,
  `leaderboards` (`api/routers/`)
- **React** — front-end ⬜ not started

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

### Running the API locally

The `api/` FastAPI layer reads Postgres credentials from the same
project-root `.env` the pipeline uses (see `.env.example`), so that file
needs to exist first -- but the API itself runs as a plain local Python
process, not against the Spark cluster, so only the `postgres` container
needs to be up:

```bash
cd docker && docker compose up -d postgres && cd ..
```

Then, from the project root, in a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate      # venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn api.main:app --reload
```

This serves the API at `http://localhost:8000` -- `GET /health` for a
liveness check, `/docs` for the interactive Swagger UI, and everything
else under the `/api/v1/` prefix (see `api/config.py`). `/docs` is the
source of truth for the current endpoint list as more get added on later
branches, rather than duplicating it here where it'd go stale.
