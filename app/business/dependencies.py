"""How a request finds "its" business.

The signed-in user comes from the Bearer token. `X-Business-Id` selects
among that user's studios; it can be omitted when they only have one.
"""

from typing import Annotated

from fastapi import Depends, Header

from app.auth.dependencies import CurrentUser
from app.business.models import BusinessProfile
from app.business.service import resolve_business
from app.core.dependencies import SessionDep

BusinessIdHeader = Annotated[
    int | None,
    Header(
        alias="X-Business-Id",
        description=(
            "Which of the signed-in user's businesses this request is for. "
            "Optional when the account has exactly one studio."
        ),
    ),
]


def get_current_business(
    session: SessionDep,
    user: CurrentUser,
    x_business_id: BusinessIdHeader = None,
) -> BusinessProfile:
    return resolve_business(session, user, x_business_id)


CurrentBusiness = Annotated[BusinessProfile, Depends(get_current_business)]
