"""
Configuration for the FastAPI layer.

Loads Postgres connection details from the project-root `.env` -- the same
file src/pipeline.py already reads via python-dotenv (see .env.example) --
so credentials are defined once and shared between the pipeline and the
API, not duplicated.

POSTGRES_DB/USER/PASSWORD are reused as-is from that .env: they're real
credentials, and must match docker/.env's values exactly (see
.env.example), same requirement the pipeline already has.

POSTGRES_HOST/POSTGRES_PORT are deliberately NOT reused from that same
.env, even though it already defines them. Those two keys describe how the
PIPELINE reaches Postgres -- host is "postgres" (the Docker Compose
service name), not "localhost" -- because a Spark JDBC write opens its
connections on the EXECUTORS, inside the spark-worker container, which can
resolve "postgres" via Docker's internal DNS but has nothing listening on
its own loopback (see src/pipeline.py's build_postgres_jdbc_url()
docstring and .env.example for the full explanation).

The API has no such split: it's one plain Python process (uvicorn) running
directly on the host, not a driver/executor pair, so it connects the way
any local client (psql, a GUI tool) does -- via the port docker-compose.yml
publishes to the host (postgres: ports: "5432:5432"), i.e. localhost:5432.
Blindly reading the pipeline's POSTGRES_HOST value here would hand the API
"postgres", which doesn't resolve outside the Docker network and would
break every local `uvicorn api.main:app --reload` run. So HOST/PORT get
their own env vars (API_DB_HOST / API_DB_PORT), separate from the
pipeline's POSTGRES_HOST/POSTGRES_PORT, defaulting to localhost:5432 for
local dev. If the API is later containerized and put on the same Docker
network as Postgres, override these two (e.g. API_DB_HOST=postgres) --
DB/USER/PASSWORD stay as-is either way.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Same explicit-path reasoning as src/pipeline.py: a bare load_dotenv()
# searches upward from the current working directory, which would do the
# wrong thing if uvicorn is ever launched from somewhere other than the
# project root. This resolves to the project root regardless of this
# file's own depth under api/.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# --------------------------------------------------------------------------
# Postgres connection
# --------------------------------------------------------------------------
POSTGRES_DB = os.environ["POSTGRES_DB"]
POSTGRES_USER = os.environ["POSTGRES_USER"]
POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]

# See the module docstring for why these are their own env vars rather than
# POSTGRES_HOST/POSTGRES_PORT.
POSTGRES_HOST = os.getenv("API_DB_HOST", "localhost")
POSTGRES_PORT = os.getenv("API_DB_PORT", "5432")

DATABASE_URL = (
    f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

# --------------------------------------------------------------------------
# API versioning
# --------------------------------------------------------------------------
# Every business-logic route (added on later branches) is mounted under
# this prefix -- see main.py. Established from the very first endpoint,
# before there's anything to version, specifically so nothing is ever
# added un-prefixed and needs a breaking move later. /health is the one
# deliberate exception -- see main.py.
API_V1_PREFIX = "/api/v1"

# --------------------------------------------------------------------------
# CORS
# --------------------------------------------------------------------------
# Env-driven rather than hardcoded, so adding a future deployed front-end
# origin (or changing the dev server's port) is a .env edit, not a code
# change + redeploy. CORS_ORIGINS is a comma-separated string (see
# .env.example) -- CORSMiddleware wants a list, so split on "," and strip
# whitespace around each entry (a stray space after a comma, e.g.
# "http://a, http://b", would otherwise become the literal, never-matching
# origin " http://b").
#
# Defaults to the Create React App dev server's default port (3000) if
# unset, so local dev still works with zero .env changes -- Vite's default
# is 5173 instead; whichever tool the front-end actually ends up using,
# override via .env rather than editing this default.
CORS_ORIGINS = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")]
