"""Import every ORM model so `Base.metadata` knows all tables.

Alembic and the test suite import this module before reading the metadata.
"""

from app.activity.models import ActivityLog
from app.business.models import BusinessProfile
from app.db.base import Base
from app.invoices.models import Invoice
from app.library.models import LibraryItem
from app.platform.models import PlatformSettings
from app.quotes.models import Quote, QuoteLine

__all__ = [
    "ActivityLog",
    "Base",
    "BusinessProfile",
    "Invoice",
    "LibraryItem",
    "PlatformSettings",
    "Quote",
    "QuoteLine",
]
