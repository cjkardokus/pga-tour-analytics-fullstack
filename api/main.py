"""
FastAPI app instance for the PGA Tour Analytics API.

Run locally (from the project root, with the Postgres container up and a
root-level .env in place -- see README.md's Setup section):

    uvicorn api.main:app --reload

Then:
  - http://localhost:8000/health        -- health check
  - http://localhost:8000/docs          -- Swagger UI
  - http://localhost:8000/api/v1/...    -- business-logic routes (courses, players, leaderboards)
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.config import API_V1_PREFIX, CORS_ORIGINS
from api.database import check_connection
from api.logging_config import configure_logging
from api.routers import courses, leaderboards, players

configure_logging()

logger = logging.getLogger("api")
request_logger = logging.getLogger("api.request")


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
# Request logging
# --------------------------------------------------------------------------
# One line per request -- method, path, status code, duration -- not one
# line per internal step. Registered before CORSMiddleware below so it
# wraps everything CORSMiddleware and the routes do (Starlette's user
# middleware stack runs in the order added, outermost first).
#
# call_next() re-raises rather than returning a response when an unhandled
# exception occurs further in (e.g. inside a route) -- that exception
# hasn't been turned into a response yet at this point in the stack; the
# global exception handler below (registered on `app`, and hence part of
# Starlette's outer ServerErrorMiddleware layer) does that. So this
# middleware has to catch-log-reraise, not just log after an ordinary
# return, to still get exactly one summary line for a request that ends
# in an unhandled exception, with the 500 it's guaranteed to become.
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (time.perf_counter() - start) * 1000
        request_logger.info("%s %s -> 500 (%.1fms)", request.method, request.url.path, duration_ms)
        raise
    duration_ms = (time.perf_counter() - start) * 1000
    request_logger.info("%s %s -> %d (%.1fms)", request.method, request.url.path, response.status_code, duration_ms)
    return response


# --------------------------------------------------------------------------
# Global exception handler
# --------------------------------------------------------------------------
# Catches anything not already handled by FastAPI's own 404 (HTTPException)
# / 422 (RequestValidationError) paths -- an unexpected bug, a dropped DB
# connection mid-request, etc. Logs the full exception server-side
# (traceback included) and returns a fixed, generic body: no raw exception
# text, no SQL, no stack trace, no file paths ever reach the client. See
# README.md's "Error handling" note and tests/test_error_handling.py --
# this turns what was previously just Starlette's default (safe, but
# unasserted) behavior into a deliberate, tested guarantee.
#
# `exc_info=exc` rather than plain `logger.exception(...)`: this handler
# runs from inside Starlette's ServerErrorMiddleware, which does call it
# from within the `except Exception as exc:` block that caught the error
# (so the ambient exc_info would likely still be correct), but passing the
# actual exception object explicitly doesn't depend on that ambient state
# still being intact by the time this coroutine actually runs.
@app.exception_handler(Exception)
async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception on %s %s", request.method, request.url.path, exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# --------------------------------------------------------------------------
# CORS
# --------------------------------------------------------------------------
# Only the React dev server (frontend/, a different origin/port) needs
# cross-origin access -- there's no other consumer. Scoped to CORS_ORIGINS
# (see config.py) rather than "*" so this doesn't silently widen into an
# open CORS policy; update CORS_ORIGINS (already env-driven) if the
# front-end's dev port or a deployed origin ever differs.
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
# first endpoint (api/routers/courses.py) so nothing was ever added
# un-prefixed and needed a breaking move to add versioning later. Each
# router module (api/routers/*.py) attaches to api_v1_router the same way,
# below.
#
# Order matters here: APIRouter.include_router() copies the target
# router's routes at call time, not lazily, so every include_router() onto
# api_v1_router below has to happen BEFORE api_v1_router itself is included
# into app -- reversing that order would silently drop whatever's included
# afterward.
api_v1_router = APIRouter(prefix=API_V1_PREFIX)
api_v1_router.include_router(courses.router)
api_v1_router.include_router(players.router)
api_v1_router.include_router(leaderboards.router)
app.include_router(api_v1_router)


# /health below is the deliberate exception: health checks conventionally
# live at the root, unversioned, since they're infrastructure (load
# balancers, container orchestrators) rather than API consumers, and
# shouldn't need updating every time the API's version does.
@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
