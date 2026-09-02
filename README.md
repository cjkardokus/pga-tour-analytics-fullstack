# pga-tour-analytics-fullstack
[![Tests](https://github.com/cjkardokus/pga-tour-analytics-fullstack/actions/workflows/tests.yml/badge.svg)](https://github.com/cjkardokus/pga-tour-analytics-fullstack/actions/workflows/tests.yml)

## Overview

A full-stack PGA Tour analytics application, end to end: a raw Kaggle
tournament-results CSV is cleaned and aggregated by a PySpark pipeline,
loaded into PostgreSQL, served by a FastAPI layer, and explored through a
React front-end. The result is three things to explore -- leaderboards
across 16 rankable stat categories, a player's career trends, and a
strokes-gained-based course difficulty ranking -- all backed by real
2017-2022 PGA Tour data.

## Tech Stack

### Pipeline
- **PySpark** -- cleans and aggregates the raw tournament data (window
  functions for per-season ranks, a season-over-season trend via `lag()`,
  groupBy aggregations for career/course rollups). This dataset's actual
  volume doesn't strictly require distributed compute -- it's chosen
  deliberately to demonstrate real distributed-processing patterns
  (partitioned window ranking, not just a pandas `.rank()`) rather than
  because the data demands it.
- **Docker Compose** -- runs a local Spark standalone cluster (one
  master, one worker) plus Postgres, so the pipeline runs against real
  infrastructure without needing a managed Spark cluster.

### Database
- **PostgreSQL** -- the pipeline's persistent output store and the API's
  data source.

### API
- **FastAPI** -- the REST layer over Postgres; its automatic OpenAPI
  schema generation is what lets the front-end generate its response
  types directly from the backend (see `openapi-typescript` below),
  rather than hand-maintaining a second copy of every model.
- **SQLAlchemy** -- Core + ORM engine (psycopg2 driver) for connection
  pooling and FastAPI's `Depends`-based session-per-request pattern;
  response shapes are still plain Pydantic models, not ORM classes.

### Frontend
- **Vite** -- dev server / build tool (not Create React App, which is
  deprecated).
- **TypeScript** -- chosen over plain JavaScript for stronger typing and
  tooling.
- **React** + **React Router** -- real URL-based routing
  (`createBrowserRouter`), not state-based view switching.
- **TanStack Query** -- data fetching/caching; chosen partly because it
  cleanly handles the debounced search-and-select pattern used
  throughout the app (the players/courses search bars, in particular)
  without hand-rolling request cancellation or race-condition handling.
- **MUI** (Material UI) -- component library and styling. MUI was chosen to ship a clean, functional,
  professional UI efficiently.
- **Recharts** -- the two Player Trends charts. Chosen over Chart.js
  specifically because it renders SVG, not canvas -- every chart element
  is real, inspectable DOM, consistent with this project's general
  approach of verifying actual rendered output rather than assuming a
  chart (or anything else) renders correctly.
- **openapi-typescript** -- generates `frontend/src/types/api.ts` from
  the backend's live OpenAPI schema, so frontend types stay in sync with
  the actual Pydantic response models automatically, rather than drifting
  out of sync with hand-maintained interfaces.

## Prerequisites

- **Python 3.14+** -- matches this project's `venv` and the version
  `.github/workflows/tests.yml` pins CI to.
- **Node.js 20+** (this project was set up against Node 24; anything
  reasonably current should work).
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

## Running the Full Stack

### Backend Setup

Create a Python virtual environment and install the pipeline/API's
dependencies:

```bash
python3 -m venv venv
source venv/bin/activate      # venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Two `.env` files are needed -- one for Docker Compose itself, one for the
pipeline/API:

```bash
cd docker && cp .env.example .env
printf 'PROJECT_ROOT=%s\nUID=%s\nGID=%s\n' "$(cd .. && pwd)" "$(id -u)" "$(id -g)" >> .env
cd ..
cp .env.example .env
```

- `docker/.env` configures the Docker Compose cluster itself: `UID`/`GID`
  run the Spark containers as *you* (so files the driver and the
  containers create under `data/` don't clash on ownership), and
  `PROJECT_ROOT` has to resolve to the same path the pipeline itself
  computes at runtime -- see `docker/README.md`'s "One-time setup" for
  why. `POSTGRES_DB`/`USER`/`PASSWORD` in this file are what the
  `postgres` container is actually initialized with.
- The project-root `.env` is what the pipeline (`src/pipeline.py`) reads
  to connect to Postgres. Its `POSTGRES_DB`/`USER`/`PASSWORD` must match
  `docker/.env`'s values exactly -- if they don't, the pipeline's write
  will fail to authenticate. It also carries `CORS_ORIGINS`, read by the
  API only: already set to `http://localhost:5173` (Vite's dev server
  port) in `.env.example`, since the front-end is real and needs it.

**A one-time host-level step, easy to miss:** add a `/etc/hosts` entry
mapping `postgres` to your own loopback address, required for the
pipeline's Postgres write to succeed (the pipeline's driver runs on your
host, not inside Docker, but still needs `postgres` to resolve):

```bash
echo '127.0.0.1 postgres' | sudo tee -a /etc/hosts
```

Skip this and `python src/pipeline.py` below fails partway through with
a hostname resolution error -- see `docker/README.md`'s "One-time setup"
section for the full explanation.

Now start the Spark + Postgres cluster:

```bash
cd docker && docker compose up -d && cd ..
```

`-d` runs it in the background; see `docker/README.md` for how to confirm
both containers started cleanly (the Spark Master UI at
`http://localhost:8080`, `docker compose ps`).

### Running the Pipeline

`src/extract.py` reads from `data/raw/pga_tour_raw.csv`, which is
gitignored and has to be downloaded before the pipeline's first run. It's
the
[pga-tour-golf-data-20152022](https://www.kaggle.com/datasets/robikscube/pga-tour-golf-data-20152022)
dataset on Kaggle -- the `kaggle` CLI (already installed via
`requirements.txt` above) can fetch it directly:

```bash
kaggle datasets download -d robikscube/pga-tour-golf-data-20152022 -p data/raw --unzip
mv "data/raw/ASA All PGA Raw Data - Tourn Level.csv" data/raw/pga_tour_raw.csv
```

This needs a one-time Kaggle API token first, if you don't already have
one -- generate one from your Kaggle account settings and save it to
`~/.kaggle/access_token`; see [Kaggle's API docs](https://www.kaggle.com/docs/api).
The `mv` above is required, not optional: the dataset is published under
that longer filename, the CLI has no rename option, and `src/extract.py`
reads the fixed path `data/raw/pga_tour_raw.csv`.

With the cluster up, both `.env` files in place, and the raw CSV
downloaded, run the pipeline:

```bash
python src/pipeline.py
```

This orchestrates extract -> transform -> load, writing
`player_season_stats` and `courses` to Postgres (the pipeline's real
downstream destination, always written). Local file export to
`data/processed/` (CSV/Parquet) is opt-in and off by default -- add
`--output-formats csv`, `--output-formats parquet`, or
`--output-formats csv,parquet` to also write one or both.

### Frontend Setup

```bash
cd frontend
npm install
```

The front-end's response types (`src/types/api.ts`) are generated from
the backend's live OpenAPI schema, not hand-written -- this requires the
API to actually be running first (the generator fetches
`http://localhost:8000/openapi.json` over HTTP, not from Python source),
so start the API (see "Running the App" below) before running:

```bash
npm run generate-types
```

Re-run this any time a backend response model changes. It's committed to
the repo (so a fresh clone has working types without needing the backend
running first) but should be treated as derived output, the same way a
lockfile is derived from `package.json`.

`VITE_API_BASE_URL` -- base URL of the FastAPI backend -- defaults to
`http://localhost:8000` when unset, matching `uvicorn`'s default port, so
local dev works with zero config. Copy `frontend/.env.example` to
`frontend/.env.local` (gitignored) to override, e.g. for a deployed
backend origin.

### Running the App

With the Postgres container up (started above) and the virtualenv active,
start the API from the project root:

```bash
uvicorn api.main:app --reload
```

This serves the API at `http://localhost:8000` -- `GET /health` for a
liveness check, `/docs` for interactive Swagger UI, everything else under
`/api/v1/`.

Then, in `frontend/`, start the dev server:

```bash
npm run dev
```

Open `http://localhost:5173`. Home links to three sections:
**Leaderboards** (configurable season/all-time panels across 16 rankable
categories -- strokes gained and counting stats like wins and cuts made),
**Player Trends** (search any player for their career stats and
season-by-season charts), and **Courses** (a strokes-gained-based
difficulty ranking of all 81 courses in the dataset).

### Running Tests

The test suite (`tests/`) runs against its own dedicated `postgres-test`
container and database -- never the real `postgres` container's
pipeline-generated data, so tests can't break just because the pipeline
re-ran and the dev data changed shape.

```bash
cd docker && docker compose up -d postgres-test && cd ..
pip install -r requirements-test.txt
pytest
```

Each test function seeds a small, fixed set of rows into `courses`/
`player_season_stats` (see `tests/fixtures.py`) before running and tears
them down after, so tests are independent of each other and of run order.

**Logging and error handling:** every request logs one line (method,
path, status code, duration) via the `api.request` logger, and the
startup DB check logs through the same consistent format (see
`api/logging_config.py`). Any exception not already handled by FastAPI's
own 404/422 paths is caught by a global handler in `api/main.py`: the
full exception is logged server-side, but the client only ever gets a
fixed `{"detail": "Internal server error"}` with a 500 -- never raw SQL,
a stack trace, or a file path. `tests/test_error_handling.py` verifies
both halves of that.

## Project Structure

```
.
├── api/               # FastAPI layer
│   ├── routers/       # courses, players, leaderboards -- one module per resource
│   └── models/        # Pydantic response models
├── src/               # PySpark pipeline: extract.py -> transform.py -> load.py, orchestrated by pipeline.py
├── docker/            # Local Spark cluster + Postgres (docker-compose.yml, init/schema.sql)
├── frontend/          # React app
│   └── src/
│       ├── api/         # fetch wrapper + TanStack Query hooks, one file per resource
│       ├── components/  # shared components (SearchBrowseList, LeaderboardTable, ErrorBoundary, ...)
│       ├── pages/       # one file per page (Home, Leaderboards, PlayerTrends, Courses) + their subcomponents/charts
│       └── types/       # generated api.ts (openapi-typescript)
├── tests/             # pytest suite for the API layer, against a dedicated test database
└── data/              # raw/processed data (gitignored)
```

## Data Source

The pipeline reads the
[pga-tour-golf-data-20152022](https://www.kaggle.com/datasets/robikscube/pga-tour-golf-data-20152022)
dataset on Kaggle: one row per (tournament, player), 2015-2022, with
finish position, strokes-gained figures by category, and tournament/
course metadata. The pipeline filters to `season > 2016` (2017 onward) --
earlier seasons have enough strokes-gained nulls to skew the per-player/
per-course averages built downstream. See "Running the Pipeline" above
for how to download it (not committed to this repo).

## Data Quality Notes

- **Conflicting duplicate rows.** 21 (tournament, player) pairs had two
  contradictory rows each (42 rows total) -- e.g. different finish
  position or strokes-gained values for what should be one player's
  result in one tournament. There's no reliable signal for which row is
  correct, so both rows are dropped for any pair that shows up more than
  once, rather than guessing.
- **A 10-tournament qualification threshold.** Average-based rankings
  (e.g. average strokes gained) require at least 10 tournaments played
  that season to receive a rank -- without it, a player with a 1-3
  tournament sample could post a misleadingly high average and rank
  ahead of full-season regulars. Cumulative-total rankings (season sums,
  wins, cuts made) have no such threshold: a low-volume player naturally
  sorts toward the bottom of a total without needing to be excluded.
- **ShotLink coverage gap.** Strokes-gained data comes from ShotLink, the
  Tour's shot-tracking system, which isn't deployed at major
  championships or international/limited-field events. 17 of the 81
  courses in the 2017-2022 dataset have zero strokes-gained data across
  every tournament hosted there. **Augusta National is a notable partial
  exception**, not one of those 17: it hosts the Masters every year in
  this range, but only shows real strokes-gained data starting in 2022
  (78 of 84 rows that year; every prior season is null). It still
  receives a real difficulty ranking, but one built from a single
  season's data rather than the 2017-2022 span most other courses draw
  on.
- **Isolated player-record gaps**, distinct from the venue-level ShotLink
  gap above -- discovered while building the player endpoints. Rory
  McIlroy's entire 2022 season (10 tournaments) has null strokes-gained
  *and* null finish-position data across every event, despite those same
  10 tournaments having real strokes-gained data for the large majority
  of other players in them (1,008 of 1,054 other-player rows). This
  isn't explained by ShotLink venue coverage -- those events (Wells Fargo
  Championship, Valero Texas Open, the Arnold Palmer Invitational, etc.)
  are ordinary domestic Tour stops with full coverage for everyone else
  -- so it reads as a gap specific to that player's records for that
  season, not the tournament.

## CI

Two parallel jobs run on every push to `main` and every PR targeting it
-- see `.github/workflows/tests.yml` (the badge at the top of this
README reflects the latest run):

- **`test`** -- the backend's pytest suite, against a plain Postgres
  *service container* (not the full `docker compose` stack -- the suite
  never touches the dev `postgres` service or the Spark cluster), with
  `docker/init/schema.sql` applied as an explicit step.
- **`frontend`** -- `npm run lint` (oxlint), `npx tsc -b` (typecheck),
  and `npm run build` for `frontend/`. See `frontend/README.md`'s own
  "CI" section.
