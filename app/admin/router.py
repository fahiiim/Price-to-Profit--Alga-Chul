from typing import Annotated

from fastapi import APIRouter, Query

from app.activity.schemas import ActivityRead
from app.activity.service import list_activity
from app.admin.schemas import AdminBusinessDetail, AdminOverview, BusinessSnapshot
from app.admin.service import get_business_detail, get_overview
from app.business.dependencies import CurrentBusiness
from app.business.models import BusinessProfile
from app.business.schemas import BusinessRead
from app.business.service import apply_platform_defaults, list_businesses
from app.core.dependencies import PaginationDep, SessionDep
from app.core.schemas import Page, error_responses
from app.platform.models import PlatformSettings
from app.platform.schemas import (
    AppSettingsRead,
    AppSettingsUpdate,
    QuoteDefaults,
    QuoteDefaultsRead,
)
from app.platform.service import (
    get_platform_settings,
    replace_quote_defaults,
    update_app_settings,
)

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    responses=error_responses(422),
)


@router.get(
    "/overview",
    response_model=AdminOverview,
    summary="Get the admin overview",
    description=(
        "Everything on the admin Overview page: this month and all-time "
        "figures, money outstanding, quote and invoice status counts, "
        "library size and the ten latest activity entries."
    ),
    response_description="Admin overview figures.",
)
def get_admin_overview(business: CurrentBusiness, session: SessionDep) -> AdminOverview:
    return get_overview(session, business)


@router.get(
    "/business",
    response_model=AdminBusinessDetail,
    summary="Get the business with usage",
    description="The business profile with its all-time usage figures.",
    response_description="Business profile and usage.",
)
def get_admin_business(
    business: CurrentBusiness, session: SessionDep
) -> AdminBusinessDetail:
    return get_business_detail(session, business)


@router.get(
    "/businesses",
    response_model=Page[BusinessSnapshot],
    summary="List businesses",
    description=(
        "Every studio that has completed first-launch setup, newest first. "
        "Does not require `X-Business-Id`. Login will restrict this later."
    ),
    response_description="A page of businesses.",
)
def list_admin_businesses(
    session: SessionDep, pagination: PaginationDep
) -> Page[BusinessSnapshot]:
    businesses, total = list_businesses(
        session, limit=pagination.limit, offset=pagination.offset
    )
    return Page[BusinessSnapshot](
        items=[
            BusinessSnapshot(
                id=row.id,
                business_name=row.business_name,
                currency=row.currency,
                has_logo=row.logo_path is not None,
                created_at=row.created_at,
            )
            for row in businesses
        ],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.get(
    "/defaults",
    response_model=QuoteDefaultsRead,
    summary="Get platform quote defaults",
    description=(
        "Defaults used to set up a **new** business profile: currency, VAT, "
        "hourly rate, markup, deposit, validity, due days and terms."
    ),
    response_description="Platform quote defaults.",
)
def get_quote_defaults(session: SessionDep) -> PlatformSettings:
    return get_platform_settings(session)


@router.put(
    "/defaults",
    response_model=QuoteDefaultsRead,
    summary="Replace platform quote defaults",
    description=(
        "Replaces every default (send the full object). Existing businesses "
        "are not changed; use **Apply defaults to the business** for that."
    ),
    response_description="The saved defaults.",
)
def replace_platform_quote_defaults(
    payload: QuoteDefaults, session: SessionDep
) -> PlatformSettings:
    return replace_quote_defaults(session, get_platform_settings(session), payload)


@router.post(
    "/defaults/apply",
    response_model=BusinessRead,
    summary="Apply defaults to the business",
    description=(
        "Copies the platform quote defaults onto the business profile, "
        "overwriting its pricing settings and terms. Existing quotes and "
        "invoices keep their own values."
    ),
    response_description="The updated business profile.",
)
def apply_defaults_to_business(
    business: CurrentBusiness, session: SessionDep
) -> BusinessProfile:
    return apply_platform_defaults(session, business, get_platform_settings(session))


@router.get(
    "/settings",
    response_model=AppSettingsRead,
    summary="Get app settings",
    description=(
        "Support contacts, legal links, app version gates and maintenance "
        "mode. The mobile app reads the same values from `GET /v1/app-config`."
    ),
    response_description="App settings.",
)
def get_platform_app_settings(session: SessionDep) -> PlatformSettings:
    return get_platform_settings(session)


@router.patch(
    "/settings",
    response_model=AppSettingsRead,
    summary="Update app settings",
    description="Partial update. Only the fields you send are changed.",
    response_description="The updated app settings.",
)
def update_platform_app_settings(
    payload: AppSettingsUpdate, session: SessionDep
) -> PlatformSettings:
    return update_app_settings(session, get_platform_settings(session), payload)


@router.get(
    "/activity",
    response_model=Page[ActivityRead],
    summary="List activity",
    description=(
        "Newest first. Every create, update, delete and status change is "
        "recorded, along with settings changes."
    ),
    response_description="A page of activity entries.",
)
def list_admin_activity(
    business: CurrentBusiness,
    session: SessionDep,
    pagination: PaginationDep,
    entity_type: Annotated[
        str | None,
        Query(
            max_length=40,
            description=(
                "Only entries about this kind of record: `business`, "
                "`library_item`, `quote`, `invoice` or `platform`."
            ),
        ),
    ] = None,
) -> Page[ActivityRead]:
    entries, total = list_activity(
        session,
        business_id=business.id,
        entity_type=entity_type,
        limit=pagination.limit,
        offset=pagination.offset,
    )
    return Page[ActivityRead](
        items=[ActivityRead.model_validate(entry) for entry in entries],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )
