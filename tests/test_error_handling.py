"""
Tests for the global exception handler (api/main.py's
handle_unexpected_exception) -- finding 3.2 of the hardening review.

Before this handler existed, an unhandled exception (e.g. a dropped DB
connection mid-request) happened to return a generic 500 with no leaked
detail purely because that's Starlette's own default ServerErrorMiddleware
behavior with debug=False -- nothing in this repo asserted that. These
tests convert "happens to be true" into "guaranteed and tested": they
deliberately trigger an unhandled exception (by pointing get_db at a
broken/unreachable engine, not by mocking the handler itself) and check
both ends of the contract -- the client-facing response, and that the
failure was actually logged server-side.
"""

import logging

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.database import get_db
from api.main import app

# Port 1 is a reserved, always-unprivileged port nothing listens on --
# connecting here fails immediately with "connection refused" rather than
# hanging, so this test doesn't need to wait out api/database.py's own
# connect_timeout to get a fast, deterministic failure.
BROKEN_DATABASE_URL = "postgresql+psycopg2://test:test@localhost:1/nonexistent"


@pytest.fixture()
def broken_db_client():
    """
    A TestClient wired to a genuinely unreachable Postgres engine via the
    same get_db dependency-override mechanism tests/conftest.py's `client`
    fixture uses for the real test database -- so hitting any endpoint
    that queries the DB raises a real sqlalchemy.exc.OperationalError from
    inside the route, left completely unhandled by the route itself, the
    same shape of failure a dropped connection mid-request would produce.

    raise_server_exceptions=False (unlike conftest.py's `client` fixture,
    which doesn't need this): TestClient's default, True, re-raises an
    unhandled exception into the TEST process instead of letting it flow
    through Starlette's ServerErrorMiddleware into a response -- which
    would defeat the point here, since what's under test is the response
    the handler produces.
    """
    broken_engine = create_engine(BROKEN_DATABASE_URL)
    broken_session_local = sessionmaker(bind=broken_engine)

    def override_get_db():
        session = broken_session_local()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app, raise_server_exceptions=False)
    finally:
        app.dependency_overrides.pop(get_db, None)
        broken_engine.dispose()


def test_unhandled_exception_returns_generic_500(broken_db_client):
    response = broken_db_client.get("/api/v1/courses/")

    assert response.status_code == 500
    # Fixed, generic body only -- no raw OperationalError text, no SQL,
    # no connection string, no stack trace, no file paths.
    assert response.json() == {"detail": "Internal server error"}

    body_text = response.text
    for leaky_substring in ("Traceback", "psycopg2", "nonexistent", ".py", "OperationalError"):
        assert leaky_substring not in body_text


def test_unhandled_exception_is_logged_server_side(broken_db_client, caplog):
    with caplog.at_level(logging.ERROR, logger="api"):
        response = broken_db_client.get("/api/v1/courses/")

    assert response.status_code == 500

    api_records = [r for r in caplog.records if r.name == "api"]
    assert len(api_records) == 1
    record = api_records[0]
    assert record.levelno == logging.ERROR
    assert "GET" in record.getMessage() and "/api/v1/courses/" in record.getMessage()
    # exc_info was attached (see main.py's handle_unexpected_exception) --
    # the full traceback is available server-side even though the client
    # never sees any of it (test_unhandled_exception_returns_generic_500
    # above).
    assert record.exc_info is not None


def test_unhandled_exception_still_logs_one_request_summary_line(broken_db_client, caplog):
    """
    The request-logging middleware (api/main.py's log_requests) has to
    produce its one-line-per-request summary even when the request ends
    in an unhandled exception, not just on the happy path -- see that
    function's own catch-log-reraise docstring/comment.
    """
    with caplog.at_level(logging.INFO, logger="api.request"):
        broken_db_client.get("/api/v1/courses/")

    request_records = [r for r in caplog.records if r.name == "api.request"]
    assert len(request_records) == 1
    message = request_records[0].getMessage()
    assert "GET" in message
    assert "/api/v1/courses/" in message
    assert "500" in message
