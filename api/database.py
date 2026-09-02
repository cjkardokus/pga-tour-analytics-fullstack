"""
Database connection/session handling for the FastAPI layer.

SQLAlchemy (Core + ORM engine, psycopg2 as the underlying driver) rather
than bare psycopg2, chosen for two reasons specific to how this will grow:

  1. FastAPI's dependency-injection model (`Depends`) pairs directly with
     SQLAlchemy's Session -- get_db() below yields one per-request and
     guarantees it's closed after, without every future route hand-rolling
     connection/cursor lifecycle and try/finally blocks itself.
  2. SessionLocal gives connection pooling for free. A plain psycopg2 setup
     would need that built by hand once request volume matters.

The trade-off is a dependency the pipeline side doesn't have (src/load.py
uses Spark's own JDBC writer, no Python DB library at all) -- but nothing
here talks to Spark or touches the pipeline's write path, so there's no
overlap to keep consistent. psycopg2-binary is still the actual driver
underneath (see requirements.txt); SQLAlchemy just sits on top of it.

Response shapes stay plain Pydantic models (see models/), not SQLAlchemy
ORM models -- the two are independent here; nothing requires them to grow
together later.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from api.config import DATABASE_URL

# connect_args below are libpq/psycopg2-level connection parameters --
# applied to every new connection the pool opens, not per-query. Both
# exist so a request fails fast with a clear error if Postgres is
# unresponsive, rather than hanging indefinitely (or for however long the
# OS's own TCP timeout happens to be, which can be minutes):
#
#   - connect_timeout (seconds): caps how long libpq waits to establish
#     the TCP connection itself. A few seconds is plenty for a local/
#     same-network Postgres -- if it takes longer than that, something is
#     actually wrong (container down, network partition), not just slow.
#   - options="-c statement_timeout=...": a libpq startup option, applied
#     server-side as a per-session GUC on every connection this engine
#     opens. Caps how long Postgres will run ANY query issued over that
#     connection before aborting it. Every query this API issues is a read
#     against a small, already-aggregated table (see api/routers/*.py) --
#     none should legitimately take anywhere near this long, so a runaway
#     or blocked query fails fast instead of holding a connection (and the
#     request) open indefinitely.
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "connect_timeout": 5,
        "options": "-c statement_timeout=5000",  # milliseconds
    },
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    FastAPI dependency: yields a Session for the lifetime of one request,
    closing it afterward regardless of whether the request succeeded.
    Usage (every route in api/routers/*.py): `db: Session = Depends(get_db)`.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_connection() -> bool:
    """
    Verifies a real connection can be established and a query executed --
    `SELECT 1` against the running Postgres container. Deliberately not
    wired to any endpoint; called from main.py's startup instead, so a
    misconfigured connection fails loudly at boot instead of on the first
    real request.
    """
    with Session(engine) as session:
        session.execute(text("SELECT 1"))
    return True
