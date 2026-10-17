from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field

Password = Field(
    min_length=8,
    max_length=128,
    description="At least 8 characters.",
    examples=["a-strong-password"],
)


class RegisterRequest(BaseModel):
    """Create an account. An OTP is sent (or returned in local) to verify the email."""

    email: EmailStr = Field(examples=["amna@glamstrands.ae"])
    name: str = Field(min_length=1, max_length=120, examples=["Amna Khan"])
    password: str = Password

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "email": "amna@glamstrands.ae",
                    "name": "Amna Khan",
                    "password": "a-strong-password",
                }
            ]
        }
    )


class VerifyOtpRequest(BaseModel):
    email: EmailStr = Field(examples=["amna@glamstrands.ae"])
    otp: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        description="Six-digit code from the registration email.",
        examples=["482193"],
    )


class ResendOtpRequest(BaseModel):
    email: EmailStr = Field(examples=["amna@glamstrands.ae"])


class LoginRequest(BaseModel):
    """Sign in after the email has been verified. Issues a session token."""

    email: EmailStr = Field(examples=["amna@glamstrands.ae"])
    password: str = Password


class RegisterPendingRead(BaseModel):
    """Registration succeeded. Verify the OTP next. No session token yet."""

    email: str
    message: str = Field(
        examples=["Enter the 6-digit code we sent to verify your email."]
    )
    otp_expires_at: datetime
    otp: str | None = Field(
        default=None,
        description=(
            "The verification code. Only included when `PTP_ENVIRONMENT` is "
            "`local`, so the app and tests can finish signup without email."
        ),
    )


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    email_verified_at: datetime | None
    created_at: datetime

    @computed_field(description="Whether the email OTP has been confirmed.")
    @property
    def email_verified(self) -> bool:
        return self.email_verified_at is not None


class TokenResponse(BaseModel):
    """Returned by login. Send `access_token` as a Bearer token."""

    access_token: str = Field(description="Opaque session token.")
    token_type: str = Field(default="bearer", examples=["bearer"])
    expires_at: datetime = Field(description="When this session stops working.")
    user: UserRead

    @classmethod
    def of(
        cls, *, access_token: str, expires_at: datetime, user: object
    ) -> "TokenResponse":
        return cls(
            access_token=access_token,
            token_type="bearer",
            expires_at=expires_at,
            user=UserRead.model_validate(user),
        )
