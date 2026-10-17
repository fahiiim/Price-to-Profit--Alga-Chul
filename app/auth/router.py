from fastapi import APIRouter, Response, status

from app.auth.dependencies import CurrentSession, CurrentUser
from app.auth.models import User
from app.auth.schemas import (
    LoginRequest,
    RegisterPendingRead,
    RegisterRequest,
    ResendOtpRequest,
    TokenResponse,
    UserRead,
    VerifyOtpRequest,
)
from app.auth.service import (
    login_user,
    logout_session,
    register_user,
    resend_otp,
    verify_otp,
)
from app.core.config import Settings
from app.core.dependencies import SessionDep, SettingsDep
from app.core.schemas import error_responses

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
    responses=error_responses(422),
)


def _reveal_otp(settings: Settings) -> bool:
    return settings.environment == "local"


@router.post(
    "/register",
    response_model=RegisterPendingRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register",
    description=(
        "Create an account with **email**, **name** and **password**. "
        "A 6-digit OTP is issued to verify the email. **No session token** "
        "is returned; call `POST /v1/auth/verify-otp`, then "
        "`POST /v1/auth/login`.\n\n"
        "If `PTP_ENVIRONMENT` is `local`, the OTP is included in the "
        "response so you can finish signup without sending email."
    ),
    response_description="Ask the user for the OTP. No access token.",
    responses=error_responses(409),
)
def register(
    payload: RegisterRequest, session: SessionDep, settings: SettingsDep
) -> RegisterPendingRead:
    return register_user(
        session,
        payload,
        otp_minutes=settings.otp_minutes,
        reveal_otp=_reveal_otp(settings),
    )


@router.post(
    "/verify-otp",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Verify the registration OTP",
    description=(
        "Confirms the email with the 6-digit code. Still does **not** sign "
        "the user in. Call `POST /v1/auth/login` with email and password next."
    ),
    responses=error_responses(409),
)
def verify_registration_otp(payload: VerifyOtpRequest, session: SessionDep) -> None:
    verify_otp(session, payload)


@router.post(
    "/resend-otp",
    response_model=RegisterPendingRead,
    summary="Resend the registration OTP",
    description="Issues a new code if the email is registered and not yet verified.",
    response_description="A new OTP window. No access token.",
    responses=error_responses(401, 409),
)
def resend_registration_otp(
    payload: ResendOtpRequest, session: SessionDep, settings: SettingsDep
) -> RegisterPendingRead:
    return resend_otp(
        session,
        payload,
        otp_minutes=settings.otp_minutes,
        reveal_otp=_reveal_otp(settings),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Sign in",
    description=(
        "Email and password. The email must already be verified with the OTP. "
        "This is the only endpoint that issues an access token."
    ),
    response_description="A session token.",
    responses=error_responses(401),
)
def login(
    payload: LoginRequest, session: SessionDep, settings: SettingsDep
) -> TokenResponse:
    return login_user(session, payload, session_days=settings.session_days)


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get the signed-in account",
    description="The account that owns the Bearer token.",
    response_description="The current user.",
    responses=error_responses(401),
)
def get_me(user: CurrentUser) -> User:
    return user


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Sign out",
    description="Revokes this session token. Other devices stay signed in.",
    responses=error_responses(401),
)
def logout(auth_session: CurrentSession, session: SessionDep) -> Response:
    logout_session(session, auth_session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
