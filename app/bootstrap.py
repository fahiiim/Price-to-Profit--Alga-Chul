"""Create the rows the application needs before it can serve requests."""

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

import app.auth.models  # noqa: F401
from app.activity.enums import ActivityAction
from app.activity.models import ActivityLog
from app.business.models import BusinessProfile
from app.core.clock import utc_now
from app.platform.service import ensure_platform_settings


def seed_required_rows(session: Session) -> None:
    """Ensure platform settings and sample studio businesses exist."""
    ensure_platform_settings(session)

    b_count = session.scalar(select(func.count()).select_from(BusinessProfile)) or 0
    if b_count < 3:
        sample_studios = [
            {
                "business_name": "Glam Strands Studio",
                "owner_name": "Amna Khan",
                "email": "hello@glamstrands.ae",
                "phone": "+971 50 123 4567",
                "currency": "AED",
                "instagram": "@glamstrands.dxb",
                "tagline": "Luxury hair extensions and master styling",
            },
            {
                "business_name": "Luxe Locks DXB",
                "owner_name": "Layla Al-Maktoum",
                "email": "team@luxelocks.ae",
                "phone": "+971 52 987 6543",
                "currency": "AED",
                "instagram": "@luxelocksdxb",
                "tagline": "Premium extensions and color matching",
            },
            {
                "business_name": "Hair by Noor",
                "owner_name": "Noor Al-Otaibi",
                "email": "noor@glamour.com",
                "phone": "+966 50 444 3322",
                "currency": "SAR",
                "instagram": "@hair.by.noor",
                "tagline": "Riyadh couture extensions",
            },
            {
                "business_name": "Strand Society",
                "owner_name": "Alice Green",
                "email": "alice@strandsociety.co.uk",
                "phone": "+44 7700 900123",
                "currency": "GBP",
                "instagram": "@strandsocietylondon",
                "tagline": "Mayfair London extensions",
            },
            {
                "business_name": "Bella Extensions",
                "owner_name": "Fatima Al-Kuwari",
                "email": "contact@bellaextensions.qa",
                "phone": "+974 3312 4567",
                "currency": "QAR",
                "instagram": "@bellaextensions.qa",
                "tagline": "Doha luxury strands",
            },
            {
                "business_name": "Mane Couture",
                "owner_name": "Sarah Jenkins",
                "email": "billing@manecouture.ae",
                "phone": "+971 55 333 7788",
                "currency": "AED",
                "instagram": "@manecouture.ad",
                "tagline": "Abu Dhabi premier salon",
            },
            {
                "business_name": "Rapunzel Tresses",
                "owner_name": "Maha Al-Harbi",
                "email": "info@rtresses.sa",
                "phone": "+966 55 888 9911",
                "currency": "SAR",
                "instagram": "@rtresses.ksa",
                "tagline": "Jeddah hair transformations",
            },
            {
                "business_name": "Velvet Hair Lab",
                "owner_name": "Chloe Martin",
                "email": "hello@velvethair.com",
                "phone": "+971 56 123 9988",
                "currency": "AED",
                "instagram": "@velvethairlab",
                "tagline": "Dubai Marina styling boutique",
            },
            {
                "business_name": "Aura Strands",
                "owner_name": "Sara Al-Sabah",
                "email": "sara@aurastrands.kw",
                "phone": "+965 9988 7766",
                "currency": "KWD",
                "instagram": "@aurastrands.kw",
                "tagline": "Kuwait custom hair extensions",
            },
        ]

        for s in sample_studios:
            existing = session.scalar(
                select(BusinessProfile).where(
                    BusinessProfile.business_name == s["business_name"]
                )
            )
            if not existing:
                biz = BusinessProfile(
                    business_name=s["business_name"],
                    owner_name=s["owner_name"],
                    email=s["email"],
                    phone=s["phone"],
                    currency=s["currency"],
                    instagram=s["instagram"],
                    tagline=s["tagline"],
                    tax_rate_percent=Decimal("5"),
                    deposit_value=Decimal("30"),
                )
                session.add(biz)
                session.flush()

                # Add initial activity log
                log = ActivityLog(
                    business_id=biz.id,
                    action=ActivityAction.BUSINESS_CREATED,
                    entity_type="business",
                    entity_id=biz.id,
                    summary="Studio subscription initialized",
                    created_at=utc_now(),
                )
                session.add(log)

    session.commit()
