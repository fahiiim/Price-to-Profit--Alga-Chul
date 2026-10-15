"""Library use cases. Every query is scoped to the given business."""

from collections.abc import Iterable

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.activity.enums import ActivityAction
from app.activity.service import record_activity
from app.business.models import BusinessProfile
from app.core.errors import BusinessRuleError, NotFoundError
from app.library.models import LibraryItem
from app.library.rules import PRICING_FIELDS, missing_fields, unrelated_fields
from app.library.schemas import LibraryItemCreate, LibraryItemUpdate
from app.pricing.enums import LineKind

ENTITY_TYPE = "library_item"


def list_items(
    session: Session,
    business: BusinessProfile,
    *,
    kind: LineKind | None = None,
    search: str | None = None,
    include_archived: bool = False,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[LibraryItem], int]:
    statement = select(LibraryItem).where(LibraryItem.business_id == business.id)
    if kind is not None:
        statement = statement.where(LibraryItem.kind == kind)
    if not include_archived:
        statement = statement.where(LibraryItem.is_archived.is_(False))
    if search:
        statement = statement.where(
            or_(
                LibraryItem.name.icontains(search, autoescape=True),
                LibraryItem.category.icontains(search, autoescape=True),
            )
        )

    total = session.scalar(select(func.count()).select_from(statement.subquery()))
    items = session.scalars(
        statement.order_by(LibraryItem.kind, LibraryItem.name, LibraryItem.id)
        .limit(limit)
        .offset(offset)
    )
    return list(items), total or 0


def get_item(session: Session, business: BusinessProfile, item_id: int) -> LibraryItem:
    item = session.scalar(
        select(LibraryItem).where(
            LibraryItem.id == item_id, LibraryItem.business_id == business.id
        )
    )
    if item is None:
        raise NotFoundError(f"Library item {item_id} was not found.")
    return item


def get_items_by_id(
    session: Session, business: BusinessProfile, item_ids: Iterable[int]
) -> dict[int, LibraryItem]:
    """Load several items at once. Raises if any ID is unknown."""
    wanted = set(item_ids)
    if not wanted:
        return {}
    items = session.scalars(
        select(LibraryItem).where(
            LibraryItem.id.in_(wanted), LibraryItem.business_id == business.id
        )
    )
    found = {item.id: item for item in items}
    missing = sorted(wanted - found.keys())
    if missing:
        raise NotFoundError(f"Library items not found: {', '.join(map(str, missing))}.")
    return found


def create_item(
    session: Session, business: BusinessProfile, payload: LibraryItemCreate
) -> LibraryItem:
    item = LibraryItem(business_id=business.id, **payload.model_dump())
    _clear_unrelated_fields(item)
    session.add(item)
    session.flush()
    record_activity(
        session,
        action=ActivityAction.LIBRARY_ITEM_CREATED,
        entity_type=ENTITY_TYPE,
        entity_id=item.id,
        summary=f"Library {item.kind} '{item.name}' added",
    )
    session.commit()
    return item


def update_item(
    session: Session, item: LibraryItem, payload: LibraryItemUpdate
) -> LibraryItem:
    changes = payload.model_dump(exclude_unset=True)
    if changes.get("name", "") is None or changes.get("kind", "") is None:
        raise BusinessRuleError("`name` and `kind` cannot be null.")

    for name, value in changes.items():
        setattr(item, name, value)
    _clear_unrelated_fields(item)

    current_values = {name: getattr(item, name) for name in PRICING_FIELDS}
    missing = missing_fields(item.kind, current_values)
    if missing:
        raise BusinessRuleError(f"`{item.kind}` items require: {', '.join(missing)}.")

    record_activity(
        session,
        action=ActivityAction.LIBRARY_ITEM_UPDATED,
        entity_type=ENTITY_TYPE,
        entity_id=item.id,
        summary=f"Library {item.kind} '{item.name}' updated",
    )
    session.commit()
    return item


def delete_item(session: Session, item: LibraryItem) -> None:
    """Delete an item. Quotes keep their own copy of the values they used."""
    record_activity(
        session,
        action=ActivityAction.LIBRARY_ITEM_DELETED,
        entity_type=ENTITY_TYPE,
        entity_id=item.id,
        summary=f"Library {item.kind} '{item.name}' deleted",
    )
    session.delete(item)
    session.commit()


def count_items_by_kind(
    session: Session, business: BusinessProfile
) -> dict[LineKind, int]:
    rows = session.execute(
        select(LibraryItem.kind, func.count())
        .where(
            LibraryItem.business_id == business.id,
            LibraryItem.is_archived.is_(False),
        )
        .group_by(LibraryItem.kind)
    )
    counts = dict.fromkeys(LineKind, 0)
    counts.update(rows.all())
    return counts


def _clear_unrelated_fields(item: LibraryItem) -> None:
    for name in unrelated_fields(item.kind):
        setattr(item, name, None)
