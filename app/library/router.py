from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.business.dependencies import CurrentBusiness
from app.core.dependencies import PaginationDep, SessionDep
from app.core.schemas import Page, error_responses
from app.library.models import LibraryItem
from app.library.schemas import LibraryItemCreate, LibraryItemRead, LibraryItemUpdate
from app.library.service import (
    create_item,
    delete_item,
    get_item,
    list_items,
    update_item,
)
from app.pricing.enums import LineKind

router = APIRouter(
    prefix="/library",
    tags=["Library"],
    responses=error_responses(422),
)


@router.get(
    "",
    response_model=Page[LibraryItemRead],
    summary="List library items",
    description=(
        "Lists saved products and services, sorted by kind then name. "
        "Archived items are hidden unless `include_archived=true`."
    ),
    response_description="A page of library items.",
)
def list_library_items(
    business: CurrentBusiness,
    session: SessionDep,
    pagination: PaginationDep,
    kind: Annotated[
        LineKind | None, Query(description="Only return items of this kind.")
    ] = None,
    search: Annotated[
        str | None,
        Query(max_length=100, description="Match against name or category."),
    ] = None,
    include_archived: Annotated[
        bool, Query(description="Include archived items.")
    ] = False,
) -> Page[LibraryItemRead]:
    items, total = list_items(
        session,
        business,
        kind=kind,
        search=search,
        include_archived=include_archived,
        limit=pagination.limit,
        offset=pagination.offset,
    )
    return Page[LibraryItemRead](
        items=[LibraryItemRead.model_validate(item) for item in items],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.post(
    "",
    response_model=LibraryItemRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a library item",
    description=(
        "Saves a reusable product or service. Which pricing fields are required "
        "depends on `kind`:\n\n"
        "| kind | required | optional |\n"
        "| --- | --- | --- |\n"
        "| `hair` | `grams_per_pack`, `pack_price` | `markup_percent` |\n"
        "| `labour` | - | `hourly_rate` |\n"
        "| `service`, `material`, `fee` | `unit_price` | `unit_cost`, "
        "`unit_label` |\n\n"
        "Pricing fields that do not apply to the kind are ignored."
    ),
    response_description="The created item.",
)
def create_library_item(
    payload: LibraryItemCreate,
    response: Response,
    business: CurrentBusiness,
    session: SessionDep,
) -> LibraryItem:
    item = create_item(session, business, payload)
    response.headers["Location"] = f"/v1/library/{item.id}"
    return item


@router.get(
    "/{item_id}",
    response_model=LibraryItemRead,
    summary="Get a library item",
    response_description="The library item.",
    responses=error_responses(404),
)
def get_library_item(
    item_id: int, business: CurrentBusiness, session: SessionDep
) -> LibraryItem:
    return get_item(session, business, item_id)


@router.patch(
    "/{item_id}",
    response_model=LibraryItemRead,
    summary="Update a library item",
    description=(
        "Partially updates an item. Set `is_archived` to hide it from the "
        "quote builder without deleting it. Existing quotes are not affected."
    ),
    response_description="The updated item.",
    responses=error_responses(404),
)
def update_library_item(
    item_id: int,
    payload: LibraryItemUpdate,
    business: CurrentBusiness,
    session: SessionDep,
) -> LibraryItem:
    item = get_item(session, business, item_id)
    return update_item(session, item, payload)


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a library item",
    description=(
        "Permanently deletes the item. Quotes that used it keep their own "
        "copy of the values, so their prices do not change."
    ),
    responses=error_responses(404),
)
def delete_library_item(
    item_id: int, business: CurrentBusiness, session: SessionDep
) -> None:
    delete_item(session, get_item(session, business, item_id))
