"""Bearer-token authentication for the signed-in stylist."""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.models import AuthSession, User
from app.auth.service import get_session_by_token
from app.core.dependencies import SessionDep
from app.core.errors import UnauthorizedError

_bearer = HTTPBearer(
    auto_error=False,
    description="Session token from `POST /v1/auth/login` after OTP verification.",
)


def get_current_session(
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> AuthSession:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Sign in to continue.")
    return get_session_by_token(session, credentials.credentials)


def get_current_user(
    auth_session: Annotated[AuthSession, Depends(get_current_session)],
) -> User:
    return auth_session.user


CurrentSession = Annotated[AuthSession, Depends(get_current_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]
