from typing import Annotated

from fastapi import APIRouter, File, UploadFile, status
from fastapi.responses import FileResponse

from app.business.dependencies import CurrentBusiness
from app.business.models import BusinessProfile
from app.business.schemas import BusinessRead, BusinessUpdate
from app.business.service import (
    remove_logo,
    resolve_logo_path,
    save_logo,
    update_business,
)
from app.core.dependencies import SessionDep, SettingsDep
from app.core.errors import NotFoundError
from app.core.schemas import error_responses

router = APIRouter(
    prefix="/business",
    tags=["Business"],
    responses=error_responses(422),
)


@router.get(
    "",
    response_model=BusinessRead,
    summary="Get the business profile",
    description=(
        "Returns the stylist's business details, branding and pricing defaults. "
        "The app loads this on start and uses the defaults to pre-fill new quotes."
    ),
    response_description="The business profile.",
)
def get_business_profile(business: CurrentBusiness) -> BusinessProfile:
    return business


@router.patch(
    "",
    response_model=BusinessRead,
    summary="Update the business profile",
    description=(
        "Partially updates the profile. Only the fields in the body are changed.\n\n"
        "Changing pricing defaults (VAT, hourly rate, markup, deposit) affects "
        "**new** quotes only. Existing quotes keep the values they were priced with."
    ),
    response_description="The updated business profile.",
)
def update_business_profile(
    payload: BusinessUpdate, business: CurrentBusiness, session: SessionDep
) -> BusinessProfile:
    return update_business(session, business, payload)


@router.put(
    "/logo",
    response_model=BusinessRead,
    summary="Upload or replace the logo",
    description=(
        "Upload a PNG, JPEG or WebP image as `multipart/form-data` in the `file` "
        "field. The logo is printed at the top of quotes, invoices and cost "
        "sheets. Any previous logo is deleted."
    ),
    response_description="The business profile with its new `logo_url`.",
    responses=error_responses(413, 415),
)
def upload_logo(
    file: Annotated[UploadFile, File(description="PNG, JPEG or WebP image.")],
    business: CurrentBusiness,
    session: SessionDep,
    settings: SettingsDep,
) -> BusinessProfile:
    data = file.file.read(settings.max_logo_bytes + 1)
    return save_logo(
        session,
        business,
        content_type=file.content_type,
        data=data,
        media_dir=settings.media_dir,
        max_bytes=settings.max_logo_bytes,
    )


@router.get(
    "/logo",
    response_class=FileResponse,
    summary="Download the logo",
    description="Returns the logo image file exactly as it was uploaded.",
    response_description="The logo image.",
    responses={
        200: {"content": {"image/png": {}, "image/jpeg": {}, "image/webp": {}}},
        **error_responses(404),
    },
)
def download_logo(business: CurrentBusiness, settings: SettingsDep) -> FileResponse:
    path = resolve_logo_path(business, settings.media_dir)
    if path is None:
        raise NotFoundError("The business has no logo.")
    return FileResponse(path)


@router.delete(
    "/logo",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove the logo",
    description="Deletes the logo. Documents are then printed without one.",
    responses=error_responses(404),
)
def delete_logo(
    business: CurrentBusiness, session: SessionDep, settings: SettingsDep
) -> None:
    remove_logo(session, business, settings.media_dir)
