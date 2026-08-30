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
from api.routers import courses

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
# All business-logic routes live under /api/v1 -- established from the
# first endpoint (api/routers/courses.py) so nothing is ever added
# un-prefixed and needs a breaking move to add versioning later. Future
# router modules (api/routers/*.py) attach to api_v1_router the same way,
# e.g. `api_v1_router.include_router(players.router)`.
#
# Order matters here: APIRouter.include_router() copies the target
# router's routes at call time, not lazily, so every include_router() onto
# api_v1_router below has to happen BEFORE api_v1_router itself is included
# into app -- reversing that order would silently drop whatever's included
# afterward.
api_v1_router = APIRouter(prefix=API_V1_PREFIX)
api_v1_router.include_router(courses.router)
app.include_router(api_v1_router)


# /health below is the deliberate exception: health checks conventionally
# live at the root, unversioned, since they're infrastructure (load
# balancers, container orchestrators) rather than API consumers, and
# shouldn't need updating every time the API's version does.
@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
