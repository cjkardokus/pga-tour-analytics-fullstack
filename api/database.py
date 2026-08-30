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

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    FastAPI dependency: yields a Session for the lifetime of one request,
    closing it afterward regardless of whether the request succeeded.
    Usage on a future route: `db: Session = Depends(get_db)`.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_connection() -> bool:
    """
    Verifies a real connection can be established and a query executed --
    `SELECT 1` against the running Postgres container. Not wired to any
    endpoint yet (scaffolding only); called from main.py's startup so a
    misconfigured connection fails loudly at boot instead of on the first
    real request.
    """
    with Session(engine) as session:
        session.execute(text("SELECT 1"))
    return True
