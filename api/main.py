"""
FastAPI app instance for the PGA Tour Analytics API.

Run locally (from the project root, with the Postgres container up and a
root-level .env in place -- see README.md's Setup section):

    uvicorn api.main:app --reload

Then:
  - http://localhost:8000/health        -- health check
  - http://localhost:8000/docs          -- Swagger UI
  - http://localhost:8000/api/v1/...    -- future business-logic routes
"""

import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import API_V1_PREFIX, CORS_ORIGINS
from api.database import check_connection

logger = logging.getLogger("api")
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Fails loudly at boot if Postgres is unreachable/misconfigured, rather
    # than on whatever request happens to hit the database first. Not a
    # business-logic endpoint -- see database.check_connection()'s
    # docstring.
    check_connection()
    logger.info("Database connection OK (SELECT 1 succeeded).")
    yield


app = FastAPI(title="PGA Tour Analytics API", lifespan=lifespan)

# --------------------------------------------------------------------------
# CORS
# --------------------------------------------------------------------------
# Only the future React dev server needs cross-origin access (this API and
# a browser app on different ports/origins) -- there's no other consumer
# yet. Scoped to CORS_ORIGINS (see config.py) rather than "*" so this
# doesn't silently widen into an open CORS policy once the API carries
# real data; update CORS_ORIGINS (or make it env-driven) if/when the
# front-end's actual dev port or a deployed origin differs.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------
# Routers
# --------------------------------------------------------------------------
# All business-logic routes live under /api/v1, established now -- via this
# router, included with zero routes on it -- even though api/routers/ is
# still empty, so nothing is ever added un-prefixed and needs a breaking
# move to add versioning later. Future router modules (api/routers/*.py)
# attach here, e.g.:
#
#   from api.routers import courses
#   api_v1_router.include_router(courses.router)
api_v1_router = APIRouter(prefix=API_V1_PREFIX)
app.include_router(api_v1_router)


# /health below is the deliberate exception: health checks conventionally
# live at the root, unversioned, since they're infrastructure (load
# balancers, container orchestrators) rather than API consumers, and
# shouldn't need updating every time the API's version does.
@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
