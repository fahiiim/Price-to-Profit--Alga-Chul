"""Account use cases. Tokens are issued only on login, after OTP verification."""

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import AuthSession, User
from app.auth.otp import OTP_MAX_ATTEMPTS, generate_otp, hash_otp
from app.auth.passwords import hash_password, verify_password
from app.auth.schemas import (
    LoginRequest,
    RegisterPendingRead,
    RegisterRequest,
    ResendOtpRequest,
    TokenResponse,
    VerifyOtpRequest,
)
from app.auth.tokens import generate_token, hash_token
from app.core.clock import utc_now
from app.core.errors import BusinessRuleError, ConflictError, UnauthorizedError

OTP_SENT_MESSAGE = "Enter the 6-digit code we sent to verify your email."


def normalize_email(email: str) -> str:
    return str(email).strip().lower()


def register_user(
    session: Session,
    payload: RegisterRequest,
    *,
    otp_minutes: int,
    reveal_otp: bool,
) -> RegisterPendingRead:
    email = normalize_email(payload.email)
    user = get_user_by_email(session, email)
    if user is not None and user.is_verified:
        raise ConflictError("An account with this email already exists.")

    if user is None:
        user = User(email=email)
        session.add(user)

    user.name = payload.name.strip()
    user.password_hash = hash_password(payload.password)
    code, expires_at = _assign_otp(user, otp_minutes=otp_minutes)
    session.commit()
    return _pending_response(email, expires_at, code, reveal_otp=reveal_otp)


def verify_otp(session: Session, payload: VerifyOtpRequest) -> None:
    user = _user_awaiting_otp(session, payload.email)
    if user.otp_expires_at is None or user.otp_expires_at <= utc_now():
        raise BusinessRuleError("The code has expired. Request a new one.")
    if user.otp_attempts >= OTP_MAX_ATTEMPTS:
        raise BusinessRuleError("Too many attempts. Request a new code.")
    if user.otp_hash != hash_otp(payload.otp):
        user.otp_attempts += 1
        session.commit()
        raise BusinessRuleError("The code is not valid.")

    user.email_verified_at = utc_now()
    _clear_otp(user)
    session.commit()


def resend_otp(
    session: Session,
    payload: ResendOtpRequest,
    *,
    otp_minutes: int,
    reveal_otp: bool,
) -> RegisterPendingRead:
    email = normalize_email(payload.email)
    user = get_user_by_email(session, email)
    if user is None:
        raise UnauthorizedError("No account exists for this email.")
    if user.is_verified:
        raise ConflictError("This email is already verified. Sign in instead.")

    code, expires_at = _assign_otp(user, otp_minutes=otp_minutes)
    session.commit()
    return _pending_response(email, expires_at, code, reveal_otp=reveal_otp)


def login_user(
    session: Session, payload: LoginRequest, *, session_days: int
) -> TokenResponse:
    user = get_user_by_email(session, normalize_email(payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise UnauthorizedError("Email or password is not correct.")
    if not user.is_verified:
        raise BusinessRuleError("Verify your email with the OTP before signing in.")
    return _issue_token(session, user, session_days=session_days)


def get_user_by_email(session: Session, email: str) -> User | None:
    return session.scalar(select(User).where(User.email == email))


def get_session_by_token(session: Session, token: str) -> AuthSession:
    if not token:
        raise UnauthorizedError("Sign in to continue.")
    row = session.scalar(
        select(AuthSession).where(AuthSession.token_hash == hash_token(token))
    )
    if row is None or row.expires_at <= utc_now():
        raise UnauthorizedError("Sign in to continue.")
    return row


def logout_session(session: Session, auth_session: AuthSession) -> None:
    session.delete(auth_session)
    session.commit()


def _user_awaiting_otp(session: Session, email: str) -> User:
    user = get_user_by_email(session, normalize_email(email))
    if user is None:
        raise BusinessRuleError("The code is not valid.")
    if user.is_verified:
        raise ConflictError("This email is already verified. Sign in instead.")
    if user.otp_hash is None:
        raise BusinessRuleError("Request a new verification code.")
    return user


def _assign_otp(user: User, *, otp_minutes: int) -> tuple[str, datetime]:
    code = generate_otp()
    user.otp_hash = hash_otp(code)
    expires_at = utc_now() + timedelta(minutes=otp_minutes)
    user.otp_expires_at = expires_at
    user.otp_attempts = 0
    return code, expires_at


def _clear_otp(user: User) -> None:
    user.otp_hash = None
    user.otp_expires_at = None
    user.otp_attempts = 0


def _pending_response(
    email: str, expires_at: datetime, code: str, *, reveal_otp: bool
) -> RegisterPendingRead:
    return RegisterPendingRead(
        email=email,
        message=OTP_SENT_MESSAGE,
        otp_expires_at=expires_at,
        otp=code if reveal_otp else None,
    )


def _issue_token(session: Session, user: User, *, session_days: int) -> TokenResponse:
    raw = generate_token()
    expires_at = utc_now() + timedelta(days=session_days)
    session.add(
        AuthSession(
            user_id=user.id,
            token_hash=hash_token(raw),
            expires_at=expires_at,
        )
    )
    session.commit()
    session.refresh(user)
    return TokenResponse.of(access_token=raw, expires_at=expires_at, user=user)
