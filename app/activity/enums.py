from enum import StrEnum


class ActivityAction(StrEnum):
    """Every change the activity log records, as `<entity>.<verb>`."""

    BUSINESS_CREATED = "business.created"
    BUSINESS_UPDATED = "business.updated"
    LOGO_UPDATED = "business.logo_updated"
    LOGO_REMOVED = "business.logo_removed"
    LIBRARY_ITEM_CREATED = "library_item.created"
    LIBRARY_ITEM_UPDATED = "library_item.updated"
    LIBRARY_ITEM_DELETED = "library_item.deleted"
    QUOTE_CREATED = "quote.created"
    QUOTE_UPDATED = "quote.updated"
    QUOTE_DUPLICATED = "quote.duplicated"
    QUOTE_STATUS_CHANGED = "quote.status_changed"
    QUOTE_DELETED = "quote.deleted"
    INVOICE_CREATED = "invoice.created"
    INVOICE_STATUS_CHANGED = "invoice.status_changed"
    INVOICE_DELETED = "invoice.deleted"
    DEFAULTS_UPDATED = "platform.defaults_updated"
    DEFAULTS_APPLIED = "platform.defaults_applied"
    APP_SETTINGS_UPDATED = "platform.app_settings_updated"
