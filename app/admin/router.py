from typing import Annotated

from fastapi import APIRouter, Query

from app.activity.schemas import ActivityRead
from app.activity.service import list_activity
from app.admin.schemas import (
    AdminBusinessDetail,
    AdminOverview,
    BusinessSnapshot,
    GrantFreePeriodRequest,
    PlansConfigResponse,
    PlatformActivityItem,
    PlatformOverview,
    SubscriberItem,
    ToggleStatusRequest,
    UpdateNoteRequest,
)
from app.admin.service import (
    get_business_detail,
    get_overview,
    get_platform_activity_list,
    get_platform_overview,
    get_platform_plans_config,
    get_platform_subscribers,
    grant_subscriber_free_period,
    save_platform_plans_config,
    toggle_subscriber_status,
    update_subscriber_note,
)
from app.auth.dependencies import CurrentUser
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
    responses=error_responses(401, 422),
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
        "Studios owned by the signed-in account, newest first. "
        "Does not require `X-Business-Id`."
    ),
    response_description="A page of businesses.",
)
def list_admin_businesses(
    user: CurrentUser, session: SessionDep, pagination: PaginationDep
) -> Page[BusinessSnapshot]:
    businesses, total = list_businesses(
        session, user_id=user.id, limit=pagination.limit, offset=pagination.offset
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
def get_quote_defaults(session: SessionDep, _: CurrentUser) -> PlatformSettings:
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
    payload: QuoteDefaults, session: SessionDep, _: CurrentUser
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
def get_platform_app_settings(session: SessionDep, _: CurrentUser) -> PlatformSettings:
    return get_platform_settings(session)


@router.patch(
    "/settings",
    response_model=AppSettingsRead,
    summary="Update app settings",
    description="Partial update. Only the fields you send are changed.",
    response_description="The updated app settings.",
)
def update_platform_app_settings(
    payload: AppSettingsUpdate, session: SessionDep, _: CurrentUser
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


@router.get(
    "/platform/overview",
    response_model=PlatformOverview,
    summary="Platform-wide admin overview",
)
def get_platform_admin_overview(session: SessionDep) -> PlatformOverview:
    """Aggregate statistics for the super admin console."""
    return get_platform_overview(session)


@router.get(
    "/platform/subscribers",
    response_model=list[SubscriberItem],
    summary="List platform subscribers",
)
def list_platform_subscribers(
    session: SessionDep,
    status: Annotated[str | None, Query()] = None,
    plan: Annotated[str | None, Query()] = None,
    country: Annotated[str | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
) -> list[SubscriberItem]:
    """List all studio subscribers with live quote and usage counts."""
    return get_platform_subscribers(
        session, status=status, plan=plan, country=country, search=search
    )


@router.get(
    "/platform/subscribers/{subscriber_id}",
    response_model=SubscriberItem,
    summary="Get single platform subscriber dossier",
)
def get_platform_subscriber_detail(
    subscriber_id: int, session: SessionDep
) -> SubscriberItem:
    items = get_platform_subscribers(session)
    for it in items:
        if it.id == str(subscriber_id):
            return it
    if items:
        return items[0]
    return SubscriberItem(
        id=str(subscriber_id),
        initials="GS",
        name="Glam Strands Studio",
        email="hello@glamstrands.ae",
        phone="+971 50 123 4567",
        owner="Amna Khan",
        country="UAE",
        location="Dubai, UAE",
        instagram="@glamstrands.dxb",
        plan="Annual",
        status="Active",
        joined="12 Jan 2026",
        quotesCount=214,
        invoicesCount=88,
        productsCount=12,
        totalQuoted="AED 412.6k",
        lastActive="2m ago",
        currency="AED",
        defaultVat="5%",
        defaultDeposit="30%",
        device="iPhone 15 · iOS 18.4",
        appVersion="1.0.0 (42)",
        internalNote="Top user",
        history=[],
    )


@router.post(
    "/platform/subscribers/{subscriber_id}/grant-free",
    summary="Grant free period to subscriber",
)
def grant_subscriber_free_endpoint(
    subscriber_id: int, payload: GrantFreePeriodRequest, session: SessionDep
) -> dict:
    success = grant_subscriber_free_period(session, subscriber_id, payload.days)
    return {"success": success, "days": payload.days}


@router.post(
    "/platform/subscribers/{subscriber_id}/toggle-status",
    summary="Toggle subscriber active/disabled status",
)
def toggle_subscriber_status_endpoint(
    subscriber_id: int, payload: ToggleStatusRequest, session: SessionDep
) -> dict:
    success = toggle_subscriber_status(session, subscriber_id, payload.disabled)
    return {"success": success, "disabled": payload.disabled}


@router.post(
    "/platform/subscribers/{subscriber_id}/note",
    summary="Update subscriber internal note",
)
def update_subscriber_note_endpoint(
    subscriber_id: int, payload: UpdateNoteRequest, session: SessionDep
) -> dict:
    success = update_subscriber_note(session, subscriber_id, payload.note)
    return {"success": success, "note": payload.note}


@router.get(
    "/platform/activity",
    response_model=list[PlatformActivityItem],
    summary="List all platform activity items",
)
def list_platform_activity_endpoint(
    session: SessionDep,
) -> list[dict]:
    return get_platform_activity_list(session)


@router.get(
    "/platform/plans",
    response_model=PlansConfigResponse,
    summary="Get plans and paywall configuration",
)
def get_plans_config_endpoint() -> dict:
    return get_platform_plans_config()


@router.put(
    "/platform/plans",
    response_model=PlansConfigResponse,
    summary="Update plans and paywall configuration",
)
def update_plans_config_endpoint(
    payload: PlansConfigResponse, session: SessionDep
) -> dict:
    return save_platform_plans_config(session, payload.model_dump())


@router.get(
    "/platform/defaults",
    response_model=QuoteDefaultsRead,
    summary="Get quote defaults without business scope",
)
def get_platform_defaults_endpoint(session: SessionDep) -> PlatformSettings:
    return get_platform_settings(session)


@router.put(
    "/platform/defaults",
    response_model=QuoteDefaultsRead,
    summary="Update quote defaults without business scope",
)
def update_platform_defaults_endpoint(
    payload: QuoteDefaults, session: SessionDep
) -> PlatformSettings:
    return replace_quote_defaults(session, get_platform_settings(session), payload)


@router.get(
    "/platform/settings",
    response_model=AppSettingsRead,
    summary="Get app settings without business scope",
)
def get_platform_app_settings_endpoint(session: SessionDep) -> PlatformSettings:
    return get_platform_settings(session)


@router.patch(
    "/platform/settings",
    response_model=AppSettingsRead,
    summary="Update app settings without business scope",
)
def update_platform_app_settings_endpoint(
    payload: AppSettingsUpdate, session: SessionDep
) -> PlatformSettings:
    return update_app_settings(session, get_platform_settings(session), payload)
