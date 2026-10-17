"""Business profile use cases: read, update, logo and document numbering."""

from pathlib import Path
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.activity.enums import ActivityAction
from app.activity.service import record_activity
from app.business.models import BusinessProfile
from app.business.schemas import REQUIRED_FIELDS, BusinessCreate, BusinessUpdate
from app.core.errors import (
    BusinessRuleError,
    FileTooLargeError,
    NotFoundError,
    UnsupportedFileTypeError,
)
from app.platform.models import PlatformSettings
from app.platform.service import copy_quote_defaults, get_platform_settings
from app.pricing.enums import DepositMode

ENTITY_TYPE = "business"
LOGO_FOLDER = "logos"
LOGO_EXTENSIONS = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}


def create_business(session: Session, payload: BusinessCreate) -> BusinessProfile:
    """Create a business from first-launch setup.

    Omitted pricing fields are copied from the platform quote defaults.
    """
    business = BusinessProfile()
    copy_quote_defaults(get_platform_settings(session), business)
    for name, value in payload.model_dump(exclude_unset=True).items():
        setattr(business, name, value)
    _ensure_valid_deposit(business)
    session.add(business)
    session.flush()

    record_activity(
        session,
        action=ActivityAction.BUSINESS_CREATED,
        entity_type=ENTITY_TYPE,
        entity_id=business.id,
        summary=f"Business '{business.business_name}' created",
        business_id=business.id,
    )
    session.commit()
    return business


def get_business(session: Session, business_id: int) -> BusinessProfile:
    business = session.get(BusinessProfile, business_id)
    if business is None:
        raise NotFoundError(f"Business {business_id} was not found.")
    return business


def list_businesses(
    session: Session, *, limit: int = 20, offset: int = 0
) -> tuple[list[BusinessProfile], int]:
    statement = select(BusinessProfile)
    total = session.scalar(select(func.count()).select_from(statement.subquery()))
    rows = session.scalars(
        statement.order_by(BusinessProfile.created_at.desc(), BusinessProfile.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(rows), total or 0


def update_business(
    session: Session, business: BusinessProfile, payload: BusinessUpdate
) -> BusinessProfile:
    changes = payload.model_dump(exclude_unset=True)
    cleared_required = sorted(
        name
        for name, value in changes.items()
        if value is None and name in REQUIRED_FIELDS
    )
    if cleared_required:
        raise BusinessRuleError(
            f"These fields cannot be null: {', '.join(cleared_required)}."
        )

    for name, value in changes.items():
        setattr(business, name, value)
    _ensure_valid_deposit(business)

    record_activity(
        session,
        action=ActivityAction.BUSINESS_UPDATED,
        entity_type=ENTITY_TYPE,
        entity_id=business.id,
        summary=f"Business profile updated: {', '.join(sorted(changes))}",
        business_id=business.id,
    )
    session.commit()
    return business


def apply_platform_defaults(
    session: Session, business: BusinessProfile, settings: PlatformSettings
) -> BusinessProfile:
    """Overwrite the business pricing defaults with the platform defaults."""
    copy_quote_defaults(settings, business)
    record_activity(
        session,
        action=ActivityAction.DEFAULTS_APPLIED,
        entity_type=ENTITY_TYPE,
        entity_id=business.id,
        summary="Platform quote defaults applied to the business profile",
        business_id=business.id,
    )
    session.commit()
    return business


def save_logo(
    session: Session,
    business: BusinessProfile,
    *,
    content_type: str | None,
    data: bytes,
    media_dir: Path,
    max_bytes: int,
) -> BusinessProfile:
    """Validate and store a new logo, replacing any previous one."""
    extension = _validate_logo(content_type, data, max_bytes)

    relative_path = Path(LOGO_FOLDER) / f"logo-{business.id}-{uuid4().hex}.{extension}"
    target = media_dir / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)

    previous = business.logo_path
    business.logo_path = relative_path.as_posix()
    record_activity(
        session,
        action=ActivityAction.LOGO_UPDATED,
        entity_type=ENTITY_TYPE,
        entity_id=business.id,
        summary="Business logo updated",
        business_id=business.id,
    )
    session.commit()
    _delete_media_file(media_dir, previous)
    return business


def remove_logo(
    session: Session, business: BusinessProfile, media_dir: Path
) -> BusinessProfile:
    previous = business.logo_path
    if previous is None:
        raise NotFoundError("The business has no logo.")

    business.logo_path = None
    record_activity(
        session,
        action=ActivityAction.LOGO_REMOVED,
        entity_type=ENTITY_TYPE,
        entity_id=business.id,
        summary="Business logo removed",
        business_id=business.id,
    )
    session.commit()
    _delete_media_file(media_dir, previous)
    return business


def resolve_logo_path(business: BusinessProfile, media_dir: Path) -> Path | None:
    """Absolute path of the logo file, or None if there is no usable logo."""
    if business.logo_path is None:
        return None
    path = media_dir / business.logo_path
    return path if path.is_file() else None


def allocate_quote_number(business: BusinessProfile) -> str:
    """Reserve the next quote number. Committed with the new quote."""
    number = f"{business.quote_prefix}-{business.next_quote_number:04d}"
    business.next_quote_number += 1
    return number


def allocate_invoice_number(business: BusinessProfile) -> str:
    """Reserve the next invoice number. Committed with the new invoice."""
    number = f"{business.invoice_prefix}-{business.next_invoice_number:04d}"
    business.next_invoice_number += 1
    return number


def _ensure_valid_deposit(business: BusinessProfile) -> None:
    if business.deposit_mode is DepositMode.PERCENT and business.deposit_value > 100:
        raise BusinessRuleError("A percentage deposit cannot be more than 100.")


def _validate_logo(content_type: str | None, data: bytes, max_bytes: int) -> str:
    """Check type, size and file signature. Returns the file extension."""
    extension = LOGO_EXTENSIONS.get(content_type or "")
    if extension is None:
        allowed = ", ".join(LOGO_EXTENSIONS)
        raise UnsupportedFileTypeError(f"Logo must be one of: {allowed}.")
    if not data:
        raise BusinessRuleError("The uploaded logo is empty.")
    if len(data) > max_bytes:
        raise FileTooLargeError(f"Logo must be at most {max_bytes} bytes.")
    if not _has_image_signature(extension, data):
        raise UnsupportedFileTypeError(
            f"The file content is not a valid {extension.upper()} image."
        )
    return extension


def _has_image_signature(extension: str, data: bytes) -> bool:
    """Compare the first bytes with the format's magic number."""
    match extension:
        case "png":
            return data.startswith(b"\x89PNG\r\n\x1a\n")
        case "jpg":
            return data.startswith(b"\xff\xd8\xff")
        case "webp":
            return data.startswith(b"RIFF") and data[8:12] == b"WEBP"
    return False


def _delete_media_file(media_dir: Path, relative_path: str | None) -> None:
    if relative_path:
        (media_dir / relative_path).unlink(missing_ok=True)
