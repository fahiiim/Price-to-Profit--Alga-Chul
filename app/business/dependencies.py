"""How a request finds "its" business.

Until login is added, the app stores the id returned by `POST /v1/businesses`
and sends it as `X-Business-Id` on every later request. Login should replace
this header with a token; only this dependency needs to change.
"""

from typing import Annotated

from fastapi import Depends, Header

from app.business.models import BusinessProfile
from app.business.service import get_business
from app.core.dependencies import SessionDep

BusinessIdHeader = Annotated[
    int,
    Header(
        alias="X-Business-Id",
        description=(
            "Which business this request belongs to. The first-launch wizard "
            "gets this from `POST /v1/businesses`. Send it on every quote, "
            "invoice, library, dashboard and profile request."
        ),
    ),
]


def get_current_business(
    session: SessionDep, x_business_id: BusinessIdHeader
) -> BusinessProfile:
    return get_business(session, x_business_id)


CurrentBusiness = Annotated[BusinessProfile, Depends(get_current_business)]
