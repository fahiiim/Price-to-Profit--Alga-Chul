"""How a request finds "its" business.

Today the backend serves one business. When per-device or per-account data is
added, only `get_current_business` needs to change; every feature already
receives the business through `CurrentBusiness`.
"""

from typing import Annotated

from fastapi import Depends

from app.business.models import BusinessProfile
from app.business.service import get_business
from app.core.dependencies import SessionDep


def get_current_business(session: SessionDep) -> BusinessProfile:
    return get_business(session)


CurrentBusiness = Annotated[BusinessProfile, Depends(get_current_business)]
