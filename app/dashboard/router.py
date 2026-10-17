from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query

from app.business.dependencies import CurrentBusiness
from app.core.dependencies import SessionDep
from app.core.errors import BusinessRuleError
from app.core.schemas import error_responses
from app.dashboard.schemas import DashboardRead
from app.dashboard.service import get_dashboard

router = APIRouter(
    prefix="/dashboard", tags=["Dashboard"], responses=error_responses(401, 422)
)


@router.get(
    "",
    response_model=DashboardRead,
    summary="Get home screen figures",
    description=(
        "Everything the app home screen shows:\n\n"
        "- **period**: quotes created, quoted value, win rate, invoices issued, "
        "money collected, profit and profit per hour for the date range "
        "(default: this month so far).\n"
        "- **outstanding**: money still owed on unpaid invoices.\n"
        "- **quote_status_counts** / **invoice_status_counts**: all-time counts.\n"
        "- **recent_quotes**: the five newest quotes.\n\n"
        "Profit figures count invoiced quotes by invoice issue date, so a "
        "quote's profit is counted once, when it is billed."
    ),
    response_description="Dashboard figures.",
)
def get_home_dashboard(
    business: CurrentBusiness,
    session: SessionDep,
    date_from: Annotated[
        date | None, Query(description="Start of the period (inclusive).")
    ] = None,
    date_to: Annotated[
        date | None, Query(description="End of the period (inclusive).")
    ] = None,
) -> DashboardRead:
    if date_from and date_to and date_from > date_to:
        raise BusinessRuleError("`date_from` must be on or before `date_to`.")
    return get_dashboard(session, business, date_from=date_from, date_to=date_to)
