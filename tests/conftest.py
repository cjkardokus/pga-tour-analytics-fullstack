"""
Shared pytest fixtures for the API test suite.

Test data strategy (see docker/docker-compose.yml's postgres-test service
for the container side of this): every test in this suite runs against a
dedicated Postgres container/database (postgres-test /
pga_tour_analytics_test), never api.database's own engine (which stays
wired to the real dev database via api/config.py). tests/fixtures.py
seeds a small, fixed, hand-verifiable set of rows into `courses` and
`player_season_stats` before every test function and truncates them
again after, so tests are independent of each other, independent of
insertion order, and independent of whatever the real pipeline-generated
dev data happens to look like on any given day.

No pytest-asyncio dependency: every route in api/routers/ is a plain
`def`, not `async def` (see courses.py/players.py/leaderboards.py --
psycopg2 is a blocking driver, so there's no async I/O happening in
them to justify it), and FastAPI's TestClient drives even async apps
through a synchronous interface regardless. Nothing here needs an event
loop of its own.
"""

import os
import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from api.database import get_db
from api.main import app
from tests.fixtures import COURSES, PLAYER_SEASONS

# Overridable via env var for CI/alternate setups; defaults to matching
# docker/docker-compose.yml's postgres-test service exactly, so a plain
# `docker compose up -d postgres-test && pytest` works with zero config.
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://test:test@localhost:5433/pga_tour_analytics_test",
)


@pytest.fixture(scope="session")
def test_engine():
    """
    Engine for postgres-test -- entirely separate from api.database's own
    engine/DATABASE_URL, which points at the real dev database and is
    never constructed, connected to, or imported by name in this file.
    """
    engine = create_engine(TEST_DATABASE_URL)

    # postgres-test's own healthcheck (docker-compose.yml) covers steady-
    # state readiness, but the container can still be finishing startup
    # the moment a test run kicks off right after `docker compose up` --
    # retry briefly rather than failing the whole suite on that race.
    last_error = None
    for _ in range(10):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            break
        except Exception as exc:  # retry on anything; the last one is raised below if none succeed
            last_error = exc
            time.sleep(1)
    else:
        raise RuntimeError(
            "Could not connect to the test database at "
            f"{TEST_DATABASE_URL!r}. Is postgres-test running? See "
            "README.md's \"Running Tests\" section."
        ) from last_error

    yield engine
    engine.dispose()


def _insert_rows(conn, table: str, rows: list[dict]) -> None:
    """Bulk-inserts `rows` (list of column-name -> value dicts, all rows
    sharing the same keys) into `table`. Column names come only from
    tests/fixtures.py's own constants, never from request/user input, so
    the f-string-built column list carries no injection risk -- same
    reasoning as api/routers/*.py's _COLUMNS constants.
    """
    if not rows:
        return
    columns = list(rows[0].keys())
    column_list = ", ".join(columns)
    placeholders = ", ".join(f":{c}" for c in columns)
    conn.execute(text(f"INSERT INTO {table} ({column_list}) VALUES ({placeholders})"), rows)


@pytest.fixture()
def db_session(test_engine):
    """
    Resets `courses`/`player_season_stats` to exactly the fixed rows in
    tests/fixtures.py before each test function, and truncates both again
    afterward.

    No wrapping-transaction-plus-rollback here, unlike the more common
    version of this pattern: every endpoint under test is read-only
    (courses.py/players.py/leaderboards.py issue nothing but SELECTs), so
    there's no app-generated write that would ever need rolling back --
    a plain commit-then-truncate is simpler and equally isolated. TRUNCATE
    (over DELETE) also resets each table's identity sequence, mostly
    useful for keeping ad-hoc psql inspection between local runs tidy,
    since every id used here is explicit either way.
    """
    with test_engine.begin() as conn:
        conn.execute(text("TRUNCATE courses, player_season_stats RESTART IDENTITY CASCADE"))
        _insert_rows(conn, "courses", COURSES)
        _insert_rows(conn, "player_season_stats", PLAYER_SEASONS)

    yield

    with test_engine.begin() as conn:
        conn.execute(text("TRUNCATE courses, player_season_stats RESTART IDENTITY CASCADE"))


@pytest.fixture()
def client(test_engine, db_session):
    """
    A FastAPI TestClient wired to the seeded test database: api.database's
    get_db dependency is overridden, for the lifetime of this fixture, to
    open sessions against `test_engine` instead of api.database.engine.

    Deliberately plain `TestClient(app)`, NOT `with TestClient(app) as
    client:` -- the context-manager form runs FastAPI's lifespan, and
    api/main.py's lifespan calls database.check_connection() against the
    real DEV database to fail loudly at boot on a bad connection (that's
    the point of it -- see its docstring). That check is unrelated to any
    endpoint under test here, and running it would make this whole suite
    depend on the real dev Postgres container being reachable -- exactly
    the coupling a dedicated test database exists to avoid. Plain
    TestClient(app) never sends the lifespan startup/shutdown ASGI
    messages, so check_connection() simply never executes.
    """
    test_session_local = sessionmaker(bind=test_engine)

    def override_get_db():
        session = test_session_local()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)
