"""Six-digit email verification codes."""

import secrets

from app.auth.tokens import hash_token

OTP_LENGTH = 6
OTP_MAX_ATTEMPTS = 5


def generate_otp() -> str:
    return f"{secrets.randbelow(10**OTP_LENGTH):0{OTP_LENGTH}d}"


def hash_otp(code: str) -> str:
    return hash_token(code.strip())
