"""Engine and session factory construction."""

from typing import Any

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


def build_engine(database_url: str) -> Engine:
    """Create an engine, applying the settings SQLite needs."""
    options: dict[str, Any] = {}
    if database_url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
        if ":memory:" in database_url:
            options["poolclass"] = StaticPool

    engine = create_engine(database_url, **options)
    if engine.dialect.name == "sqlite":
        event.listen(engine, "connect", _enable_sqlite_foreign_keys)
    return engine


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create the factory used to open one session per request."""
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def _enable_sqlite_foreign_keys(dbapi_connection: Any, _: Any) -> None:
    """SQLite ignores foreign keys unless enabled on every connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
