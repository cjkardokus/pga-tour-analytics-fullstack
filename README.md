# pga-tour-analytics-fullstack
[![Tests](https://github.com/cjkardokus/pga-tour-analytics-fullstack/actions/workflows/tests.yml/badge.svg)](https://github.com/cjkardokus/pga-tour-analytics-fullstack/actions/workflows/tests.yml)

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

## Prerequisites

- **Python 3.14+** -- matches this project's `venv` and the version
  `.github/workflows/tests.yml` pins CI to.
- **Docker**, with Compose -- runs the Spark cluster and both Postgres
  containers (see `docker/README.md`).
- **A Unix-like shell: native Linux, macOS, or WSL2 on Windows.** Setup
  below relies on `id -u`/`id -g` and a `/etc/hosts` edit, and
  `docker-compose.yml` bind-mounts the host's own `/etc/passwd`/`/etc/group`
  into the Spark containers -- confirmed working on native Linux and
  WSL2, unverified on macOS (see that file's top comment), and not
  supported as written on plain Windows without WSL. `docker/README.md`'s
  Spark memory sizing also assumes a WSL2-style RAM cap; adjust
  `mem_limit`/`cpus` in `docker-compose.yml` if your host has more to work
  with.

## Setup

The PySpark pipeline runs against a local Docker Spark cluster and a
Postgres container -- see `docker/README.md` for full one-time setup and
starting/stopping the cluster. In short, before first run:

- `docker/.env` (from `docker/.env.example`) -- configures the Docker
  Compose cluster itself (Spark bind-mount paths, Postgres credentials).
- `.env` at the project root (from `.env.example`) -- read by the pipeline
  itself to connect to Postgres. `POSTGRES_DB`/`USER`/`PASSWORD` here must
  match `docker/.env`'s values exactly. Also carries `CORS_ORIGINS`, read
  by the API only (see "Running the API locally" below) -- defaults to
  `http://localhost:3000` if unset, so it's safe to leave out until a
  front-end origin actually needs adding.
- **A one-time host-level step, easy to miss:** a `/etc/hosts` entry
  mapping `postgres` to your own loopback address, required for the
  pipeline's Postgres write to succeed. This isn't a file in this repo --
  see `docker/README.md`'s "One-time setup" section for the exact command
  and why it's needed. Skip it and `python src/pipeline.py` below fails
  partway through with a hostname resolution error, which is a confusing
  thing to debug blind if you don't already know this step exists.

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

**Logging and error handling:** every request logs one line (method,
path, status code, duration) via the `api.request` logger, and the
startup DB check logs through the same consistent format (see
`api/logging_config.py`) -- plain text, not JSON, which is intentionally
enough at this project's size. Any exception not already handled by
FastAPI's own 404/422 paths (an unexpected bug, a dropped DB connection
mid-request, etc.) is caught by a global handler in `api/main.py`: the
full exception is logged server-side, but the client only ever gets a
fixed `{"detail": "Internal server error"}` with a 500 -- never raw SQL,
a stack trace, or a file path. `tests/test_error_handling.py` verifies
both halves of that by deliberately pointing a request at an unreachable
database. Both the DB connection attempt itself and any query issued
against it are timeout-bounded (`api/database.py`) so a hung Postgres
fails a request fast rather than hanging it indefinitely.

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

### CI

This same suite runs automatically on every push to `main` and every PR
targeting it -- see `.github/workflows/tests.yml` (the badge at the top
of this README reflects the latest run). It uses a plain Postgres
*service container* rather than the full `docker compose` stack above --
the test suite never touches the dev `postgres` service or the Spark
cluster, so there's nothing for either to do in CI -- with
`docker/init/schema.sql` applied as an explicit step rather than via
Postgres's own init-script mechanism, since GitHub Actions starts service
containers before the repo is even checked out (see the workflow file's
own comments for why that rules out a volume-mounted init script here).
