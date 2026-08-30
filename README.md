# pga-tour-analytics-fullstack
A full-stack PGA Tour analytics application: PySpark data pipeline → PostgreSQL → FastAPI → React.

## Status
The PySpark pipeline and its Postgres store are complete and working
end-to-end. The FastAPI layer's data-facing surface is complete --
`courses`, `players`, and `leaderboards` cover everything in the current
schema -- and now has an automated test suite (`tests/`) running against
a dedicated test database, independent of the real pipeline-generated
data. The API as a whole still has no auth or deployment story yet, and
the React front-end hasn't been started.

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
  match `docker/.env`'s values exactly. Also carries `CORS_ORIGINS`, read
  by the API only (see "Running the API locally" below) -- defaults to
  `http://localhost:3000` if unset, so it's safe to leave out until a
  front-end origin actually needs adding.

### Getting the data

`src/extract.py` reads from `data/raw/pga_tour_raw.csv`, which is
gitignored (not committed -- see `.gitignore`) and has to be downloaded
before the pipeline's first run. It's the
[pga-tour-golf-data-20152022](https://www.kaggle.com/datasets/robikscube/pga-tour-golf-data-20152022)
dataset on Kaggle. The `kaggle` CLI (one of `requirements.txt`'s runtime
dependencies -- see "Running the API locally" below for the virtualenv
setup, or `pip install kaggle` on its own to fetch the data ahead of that)
can fetch it directly:

```bash
kaggle datasets download -d robikscube/pga-tour-golf-data-20152022 -p data/raw --unzip
mv "data/raw/ASA All PGA Raw Data - Tourn Level.csv" data/raw/pga_tour_raw.csv
```

This needs a one-time Kaggle API token first, if you don't already have
one: an API token generated from your Kaggle account settings, saved to
`~/.kaggle/access_token`. See
[Kaggle's API docs](https://www.kaggle.com/docs/api) for how to generate
one.

The dataset itself is published under that longer filename (`ASA All PGA
Raw Data - Tourn Level.csv`) -- the CLI has no rename option, so the `mv`
above is required, not optional: `src/extract.py` reads the fixed path
`data/raw/pga_tour_raw.csv` and won't find the file under its
as-downloaded name.

Once the cluster is up, both `.env` files are in place, and the raw CSV is
downloaded:

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

### Running tests

The test suite (`tests/`) runs against its own dedicated `postgres-test`
container and database -- never the real `postgres` container's
pipeline-generated data, so tests can't break just because the pipeline
re-ran and the dev data changed shape. Start it (no `.env` needed; its
credentials are hardcoded in docker-compose.yml, since it never holds
anything but the tests' own seeded rows):

```bash
cd docker && docker compose up -d postgres-test && cd ..
```

Then, with the virtualenv from above active, install the test-only
dependencies on top of `requirements.txt` (`requirements-test.txt` pulls
that in itself, so this one line covers both):

```bash
pip install -r requirements-test.txt
pytest
```

Each test function seeds a small, fixed set of rows into `courses`/
`player_season_stats` (see `tests/fixtures.py`) before running and tears
them down after, so tests are independent of each other and of run order.
`postgres-test`'s data directory is tmpfs-backed, so a plain
`docker compose stop postgres-test` (or a machine restart) leaves nothing
behind to clean up later.
