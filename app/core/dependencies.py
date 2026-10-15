"""Request-scoped FastAPI dependencies shared by every feature."""

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.config import Settings


def get_session(request: Request) -> Iterator[Session]:
    """Open one database session per request and close it afterwards."""
    session_factory = request.app.state.session_factory
    with session_factory() as session:
        yield session


def get_app_settings(request: Request) -> Settings:
    """Return the settings the running application was created with."""
    return request.app.state.settings


@dataclass(frozen=True, slots=True)
class Pagination:
    limit: int
    offset: int


def get_pagination(
    limit: Annotated[
        int, Query(ge=1, le=100, description="Maximum records to return.")
    ] = 20,
    offset: Annotated[int, Query(ge=0, description="Number of records to skip.")] = 0,
) -> Pagination:
    """Read the standard `limit` and `offset` query parameters."""
    return Pagination(limit=limit, offset=offset)


SessionDep = Annotated[Session, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_app_settings)]
PaginationDep = Annotated[Pagination, Depends(get_pagination)]
