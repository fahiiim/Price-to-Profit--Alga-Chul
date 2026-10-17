# Technical Reference

This document describes every folder, file, class and function in the
backend, **who calls what**, and **how data moves** from an HTTP request to the
database and back. Read it top to bottom once; afterwards use it as a lookup.

- For setup and the API summary see the [README](../README.md).
- For the order the code was written in see the [Build Guide](BUILD_GUIDE.md).

## Contents

1. [Architecture in one page](#1-architecture-in-one-page)
2. [Dependency rules between packages](#2-dependency-rules-between-packages)
3. [Life of a request](#3-life-of-a-request)
4. [Application wiring](#4-application-wiring-app)
5. [`app/core` — shared building blocks](#5-appcore--shared-building-blocks)
6. [`app/db` — database layer](#6-appdb--database-layer)
7. [`app/pricing` — pure pricing engine](#7-apppricing--pure-pricing-engine)
8. [`app/activity` — activity log](#8-appactivity--activity-log)
9. [`app/platform` — platform settings](#9-appplatform--platform-settings)
10. [`app/business` — business profile](#10-appbusiness--business-profile)
11. [`app/library` — saved items](#11-applibrary--saved-items)
12. [`app/quotes` — quotes](#12-appquotes--quotes)
13. [`app/invoices` — invoices](#13-appinvoices--invoices)
14. [`app/documents` — PDFs](#14-appdocuments--pdfs)
15. [`app/dashboard` — figures](#15-appdashboard--figures)
16. [`app/admin` — owner dashboard](#16-appadmin--owner-dashboard)
17. [`migrations` — Alembic](#17-migrations--alembic)
18. [`tests`](#18-tests)
19. [End-to-end data flows](#19-end-to-end-data-flows)
20. [Database schema](#20-database-schema)

---

## 1. Architecture in one page

The code is organised **by feature**, not by technical layer. Each feature
folder owns its tables, its request/response shapes, its use cases and its
HTTP endpoints:

| File | Responsibility | Knows about HTTP? | Knows about the DB? |
|---|---|---|---|
| `router.py` | Endpoints: parse the request, call the service, shape the response, document it for OpenAPI | Yes | Only through the injected `Session` |
| `schemas.py` | Pydantic models for request bodies and responses, with validation and examples | No | No (some have `from_model` helpers that read ORM objects) |
| `service.py` | Use cases: queries, rules, writes, activity log, `commit()` | No | Yes |
| `models.py` | SQLAlchemy tables | No | Yes |
| `policy.py` / `rules.py` | Pure business rules (status transitions, required fields) | No | No |

Shared code sits in three places:

- `app/core` — configuration, time, errors, error envelope, shared schema
  types, FastAPI dependencies, OpenAPI text.
- `app/db` — declarative base, engine/session, exact column types.
- `app/pricing` — the pricing engine. Pure Python: it imports nothing from
  FastAPI, SQLAlchemy or other features, so it can be unit-tested and reused
  anywhere.

```text
                   ┌──────────────────────────────────────────────┐
HTTP request ────► │ router.py   (FastAPI, dependencies, schemas) │
                   └──────────────┬───────────────────────────────┘
                                  │ Pydantic payload + Session + BusinessProfile
                   ┌──────────────▼───────────────────────────────┐
                   │ service.py  (use case, one transaction)      │──► activity.record_activity
                   └──────┬────────────────┬──────────────────────┘
                          │                │
               ┌──────────▼─────┐   ┌──────▼──────────┐
               │ policy / rules │   │ app.pricing     │   (pure, no I/O)
               └────────────────┘   └─────────────────┘
                          │
                   ┌──────▼──────────────┐
                   │ models.py (ORM)     │──► SQLite via app.db
                   └─────────────────────┘
```

---

## 2. Dependency rules between packages

Imports only point "down" this list. Nothing lower imports anything higher,
which is why there are no import cycles.

```text
app.main → app.factory → app.api → feature routers
admin        → dashboard, library, business, platform, activity
documents    → invoices, quotes, business
dashboard    → invoices, quotes, business
invoices     → quotes, business, activity
quotes       → library, business, activity, pricing
library      → business (model only), activity, pricing
business     → platform, activity, pricing
platform     → activity, pricing
activity     → core, db
pricing      → (nothing)
core, db     → pricing.money / pricing.errors only
```

Two deliberate choices keep this clean:

- `core/errors.py` has no FastAPI import. The exception → HTTP translation
  lives in `core/handlers.py`, which is only used by `factory.py`.
- `platform` does not import `business`. Seeding both rows is coordinated by
  `app/bootstrap.py`, which sits above both.

---

## 3. Life of a request

Example: `POST /v1/quotes` with the worked example body.

1. **Uvicorn** calls the ASGI app built by `app.factory.create_app`
   (exported as `app.main.app`).
2. **CORS middleware** runs, then FastAPI matches the route registered by
   `app/quotes/router.py` under the `/v1` prefix from `app/api.py`.
3. **Dependencies resolve** (from `core/dependencies.py` and
   `business/dependencies.py`):
   - `SessionDep` → `get_session` opens a SQLAlchemy `Session` from
     `request.app.state.session_factory` and closes it after the response.
   - `CurrentUser` → Bearer token → `auth.service.get_session_by_token`.
   - `CurrentBusiness` → that user's studio (`X-Business-Id` if they have
     more than one).
4. **Validation**: FastAPI validates the JSON into `QuoteCreate`
   (`quotes/schemas.py`). Money fields use `core.schemas.Money`, which parses
   decimals and rounds them half-up to 2 dp. A failure raises
   `RequestValidationError` → `core/handlers.py` returns the `validation_error`
   envelope (422).
5. **Router → service**: `create_new_quote` calls
   `quotes.service.create_quote(session, business, payload)`.
6. **Line resolution**: `quotes.line_resolver.resolve_lines` loads linked
   library items in one query (`library.service.get_items_by_id`) and fills in
   every missing value (line → library item → business default), producing
   `ResolvedLine` objects holding pure pricing inputs (`HairLine`,
   `LabourLine`, `ItemLine`).
7. **Pricing**: `app.pricing.price_quote` returns a `PricedQuote` (per-line
   `LineResult`s + `QuoteTotals`).
8. **Persistence**: the service builds `Quote` + `QuoteLine` rows, allocates
   the number with `business.service.allocate_quote_number`, flushes, calls
   `activity.service.record_activity`, and `commit()`s **once**.
9. **Response**: the router sets `Location: /v1/quotes/{id}` and returns
   `QuoteRead.from_model(quote)`; FastAPI serialises decimals as strings.
10. Any `ApplicationError` or `PricingError` raised along the way is turned
    into the error envelope by `core/handlers.py`.

---

## 4. Application wiring (`app/`)

### `app/main.py`
ASGI entry point. `app = create_app()`. Used by `uvicorn app.main:app`.

### `app/factory.py`
**`create_app(settings: Settings | None = None) -> FastAPI`** — the
composition root.

- Builds the engine (`db.session.build_engine`) and session factory
  (`db.session.build_session_factory`) from `settings.database_url`.
- Defines the **lifespan**: creates `settings.media_dir`, opens a session and
  calls `bootstrap.seed_required_rows`, and disposes the engine on shutdown.
- Creates `FastAPI` with the long description and tags from `core/openapi.py`,
  `generate_unique_id_function=operation_id` (operation IDs = function names)
  and Swagger UI options (collapsed sections, filter, request duration,
  try-it-out enabled).
- Stores `settings`, `engine`, `session_factory` on **`app.state`**. This is
  how dependencies reach them, and why tests can run against any database.
- Adds CORS (exposing `Content-Disposition` and `Location`), registers the
  exception handlers, includes the health router and the `/v1` API router.

Used by: `app/main.py`, `tests/conftest.py`, and the scripts you write.

### `app/api.py`
`api_router = APIRouter(prefix="/v1")` including the routers of `platform`,
`business`, `library`, `quotes`, `invoices`, `documents`, `dashboard` and
`admin`. Used by `factory.py`.

### `app/bootstrap.py`
**`seed_required_rows(session)`** — calls
`platform.service.ensure_platform_settings` and commits. Businesses are
created through `POST /v1/businesses`, not seeded. Idempotent. Used by the
lifespan in `factory.py`.

### `app/health.py`
| Name | Kind | Purpose |
|---|---|---|
| `LiveStatus` | schema | `status`, `version`, `environment` |
| `ReadyStatus` | schema | `status`, `database` |
| `live(settings)` | `GET /health/live` | Process is up; no I/O |
| `ready(session)` | `GET /health/ready` | Runs `SELECT 1` against the database |

---

## 5. `app/core` — shared building blocks

### `core/config.py`
- **`PROJECT_ROOT`** — repository root, used for default paths.
- **`Settings(BaseSettings)`** — `app_name`, `app_version`, `environment`,
  `database_url`, `media_dir`, `max_logo_bytes`, `cors_origins`. Reads
  `PTP_*` environment variables and `.env`.
- **`get_settings()`** — cached singleton (`lru_cache`).

Used by: `factory.py` (default settings), `core/dependencies.py`
(`SettingsDep` type), `migrations/env.py` (database URL), tests (custom
settings).

### `core/clock.py`
- **`utc_now() -> datetime`** — timezone-aware UTC now.
- **`today() -> date`** — UTC date.

The only source of "now" in the code. Used by `db/base.py` (timestamps),
`activity/models.py`, and the quotes, invoices, dashboard and admin services
(validity dates, `sent_at`, `paid_at`, default periods).

### `core/errors.py`
Framework-free exceptions for expected failures. Services raise them; they
never import HTTP status codes.

| Class | HTTP | `code` | Typical source |
|---|---|---|---|
| `ApplicationError` | base | — | Carries `message` |
| `NotFoundError` | 404 | `not_found` | `get_quote`, `get_item`, `get_invoice`, missing logo |
| `ConflictError` | 409 | `conflict` | Editing an invoiced quote, illegal status change, double invoicing |
| `BusinessRuleError` | 422 | `business_rule_violation` | Missing line fields, bad deposit, due date before issue date |
| `FileTooLargeError` | 413 | `file_too_large` | Logo upload |
| `UnsupportedFileTypeError` | 415 | `unsupported_file_type` | Logo upload |

### `core/handlers.py`
- **`error_body(code, message, details=None)`** — builds
  `{"error": {"code", "message", "details"}}`.
- **`register_exception_handlers(app)`** — registers three handlers:
  `ApplicationError` (maps class → status/code), `PricingError` (422
  `pricing_error`) and `RequestValidationError` (422 `validation_error` with
  `details` = one entry per invalid field, `loc`/`msg`/`type`).

Used by `factory.py`.

### `core/schemas.py`
Field types reused by every feature's schemas:

| Name | Definition | Used for |
|---|---|---|
| `TwoDecimals` | `AfterValidator(round_money)` | Normalises any decimal input to 2 dp |
| `Money` | `Decimal ≥ 0`, 2 dp | Prices, costs, rates, deposit values |
| `Percent` | `0 ≤ Decimal ≤ 100`, 2 dp | Tax rate, deposit percent |
| `MarkupPercent` | `0 ≤ Decimal ≤ 1000`, 2 dp | Hair markup |
| `Grams`, `Hours`, `Quantity` | `Decimal > 0`, 2 dp | Line quantities |
| `HttpLink` | `HttpUrl` serialised as `str` | Website, payment link, legal URLs |

Response helpers:

- **`ErrorDetail`, `ErrorBody`, `ErrorResponse`** — OpenAPI models of the
  error envelope.
- **`Page[ItemT]`** — generic list page: `items`, `total`, `limit`, `offset`.
- **`error_responses(*status_codes)`** — returns the `responses=` mapping for
  a route so `/docs` shows every possible error with its envelope schema.

### `core/dependencies.py`
| Name | Returns | Notes |
|---|---|---|
| `get_session(request)` | `Iterator[Session]` | Opens a session from `app.state.session_factory` and closes it after the request |
| `get_app_settings(request)` | `Settings` | Reads `app.state.settings` (so tests' settings win) |
| `Pagination` | dataclass | `limit`, `offset` |
| `get_pagination(limit, offset)` | `Pagination` | `limit` 1–100 (default 20), `offset ≥ 0` |
| `SessionDep`, `SettingsDep`, `PaginationDep` | `Annotated` aliases | What routers declare as parameters |

### `core/openapi.py`
- **`API_DESCRIPTION`** — the Markdown shown at the top of `/docs` and
  `/redoc`: money rules, pagination, error table, typical flow, scope.
- **`OPENAPI_TAGS`** — order and description of each section (Health, App
  config, Business, Library, Quotes, Invoices, Documents, Dashboard, Admin).
- **`operation_id(route)`** — uses the route function name as the
  `operationId`, giving clean names to generated API clients. Route function
  names are therefore unique across the app.

---

## 6. `app/db` — database layer

### `db/types.py`
- **`ScaledDecimal(scale=2)`** — a `TypeDecorator` that stores a `Decimal` as
  an **integer** in its smallest unit (`2104.00` → `210400`). SQLite has no
  exact decimal type; integers keep `SUM()` exact. `scale=4` is used for
  `cost_per_gram`. Bind: `Decimal` → scaled `int` (half-up). Result: `int` →
  `Decimal` with the right exponent.
- **`UTCDateTime`** — stores naive UTC, returns aware UTC datetimes.
- **`str_enum(enum_class)`** — a non-native `Enum` column that stores the
  **values** (`"draft"`), not the member names, with a length check.

Used by every `models.py`.

### `db/base.py`
- **`NAMING_CONVENTION`** — deterministic names for indexes and constraints
  (required for Alembic batch mode on SQLite).
- **`Base(DeclarativeBase)`** — metadata with that convention.
- **`TimestampMixin`** — `created_at` / `updated_at` (`UTCDateTime`, set from
  `clock.utc_now`, `updated_at` refreshed on update).

### `db/session.py`
- **`build_engine(database_url)`** — for SQLite sets
  `check_same_thread=False`, uses `StaticPool` for in-memory databases (so
  every session sees the same database in tests) and registers
  `_enable_sqlite_foreign_keys` so `PRAGMA foreign_keys=ON` is run on every
  connection (enforces `CASCADE`/`RESTRICT`).
- **`build_session_factory(engine)`** — `sessionmaker(expire_on_commit=False)`
  so objects stay readable after `commit()` when the router serialises them.

Used by `factory.py` and `migrations/env.py`.

### `db/registry.py`
Imports every `models.py` and re-exports `Base`. Importing it guarantees
`Base.metadata` contains all tables. Used by `migrations/env.py` (autogenerate)
and `tests/conftest.py` (`create_all`).

---

## 7. `app/pricing` — pure pricing engine

No I/O, no framework imports. Everything is a frozen, slotted dataclass or a
function of `Decimal`s.

### `pricing/enums.py`
- **`LineKind`** — `hair`, `labour`, `service`, `material`, `fee`.
- **`DepositMode`** — `percent`, `fixed`.

Shared vocabulary for pricing, library items, quote lines and defaults.

### `pricing/errors.py`
- **`PricingError(ValueError)`** — invalid numbers (zero pack size, negative
  price…). Mapped to 422 `pricing_error` by `core/handlers.py`.

### `pricing/money.py`
| Name | Meaning |
|---|---|
| `ZERO`, `HUNDRED`, `CENT`, `RATE_QUANTUM` | Decimal constants (`CENT = 0.01`, `RATE_QUANTUM = 0.0001`) |
| `round_money(value)` | Half-up to 2 dp |
| `round_rate(value)` | Half-up to 4 dp (cost per gram) |
| `percent_of(amount, percent)` | `round_money(amount × percent / 100)` |

Used by `core/schemas.py` (input normalisation), `invoices/policy.py`,
`library/schemas.py`, `dashboard/service.py`, `documents/builders.py`,
`quotes/line_resolver.py`.

### `pricing/calculator.py`
Inputs:

| Class | Fields |
|---|---|
| `HairLine` | `grams_required`, `grams_per_pack`, `pack_price`, `markup_percent`, `whole_packs=True`, `taxable=True` |
| `LabourLine` | `hours`, `hourly_rate`, `taxable=True` |
| `ItemLine` | `quantity`, `unit_price`, `unit_cost=0`, `taxable=True` |
| `LineInput` | type alias: `HairLine \| LabourLine \| ItemLine` |
| `Deposit` | `mode`, `value` |

Outputs:

| Class | Fields |
|---|---|
| `LineResult` | `price`, `cost`, `taxable`, `hours`, `cost_per_gram`, `packs_needed`, `leftover_grams` |
| `QuoteTotals` | `subtotal`, `taxable_amount`, `tax_amount`, `total`, `deposit_amount`, `balance_due`, `total_cost`, `profit`, `labour_hours`, `profit_per_hour`, `margin_percent` |
| `PricedQuote` | `lines: tuple[LineResult, ...]`, `totals: QuoteTotals` |

Functions:

| Function | What it does |
|---|---|
| `price_hair(line)` | `cost_per_gram = pack_price / grams_per_pack`; `packs = ceil(grams_required / grams_per_pack)`; whole packs → `cost = packs × pack_price`, `leftover = packs × pack size − required`; otherwise `cost = grams × cost_per_gram`; `price = cost × (1 + markup/100)`. Both rounded. |
| `price_labour(line)` | `price = hours × hourly_rate`, `cost = 0`, `hours` reported for profit per hour |
| `price_item(line)` | `price = quantity × unit_price`, `cost = quantity × unit_cost` |
| `price_line(line)` | `match` on the input type → one of the three above |
| `calculate_deposit(total, deposit)` | percent → `percent_of(total, value)`; fixed → `value`; capped at `total`; `None` → 0 |
| `calculate_totals(lines, *, tax_rate_percent, deposit)` | Sums rounded lines; tax on taxable lines only; profit = subtotal − cost; profit per hour and margin are `None` when their divisor is 0 |
| `price_quote(lines, *, tax_rate_percent, deposit)` | `price_line` for each line, then `calculate_totals` |
| `_ensure_positive`, `_ensure_non_negative`, `_ensure_at_most` | Raise `PricingError` with the field name |

### `pricing/__init__.py`
Re-exports the public names above. Callers use `from app.pricing import …`.

Used by: `quotes/line_resolver.py` (builds inputs), `quotes/service.py`
(`price_quote`, `Deposit`), tests.

---

## 8. `app/activity` — activity log

An append-only list of important changes, shown on the admin dashboard.

| File | Contents |
|---|---|
| `enums.py` | `ActivityAction` — `business.updated`, `business.logo_updated`, `business.logo_removed`, `library_item.created/updated/deleted`, `quote.created/updated/duplicated/status_changed/deleted`, `invoice.created/status_changed/deleted`, `platform.defaults_updated/defaults_applied/app_settings_updated` |
| `models.py` | `ActivityLog` — `id`, `action`, `entity_type`, `entity_id`, `summary`, `created_at` |
| `schemas.py` | `ActivityRead` — response model |
| `service.py` | `record_activity(session, *, action, entity_type, entity_id, summary)` — **adds** a row without committing, so it is saved in the same transaction as the change it describes. `list_activity(session, *, entity_type, limit, offset)` — newest first, with total count |

`record_activity` is called by every write in the business, library, quotes,
invoices and platform services. `list_activity` is used by
`admin/router.py` and `admin/service.py`.

---

## 9. `app/platform` — platform settings

One row (`id = 1`) owned by the admin: the **quote defaults** given to new
businesses and the **mobile app configuration**.

### `platform/models.py`
- **`DEFAULT_QUOTE_TERMS`, `DEFAULT_INVOICE_TERMS`** — starting terms text.
- **`QuoteDefaultsMixin`** — columns shared by the platform row and the
  business profile: `currency`, `tax_label`, `tax_rate_percent`,
  `hourly_rate`, `default_markup_percent`, `deposit_mode`, `deposit_value`,
  `whole_packs_default`, `quote_validity_days`, `invoice_due_days`,
  `quote_terms`, `invoice_terms`.
- **`PlatformSettings(QuoteDefaultsMixin, TimestampMixin, Base)`** — adds
  `support_email`, `support_whatsapp`, `terms_url`, `privacy_url`,
  `minimum_app_version`, `latest_app_version`, `maintenance_mode`,
  `maintenance_message`.

`QuoteDefaultsMixin` is reused by `business/models.py`, which is how the two
rows share exactly the same default fields.

### `platform/schemas.py`
| Class | Purpose |
|---|---|
| `QuoteDefaults` | Full set of default fields; `_check_deposit` rejects a percent deposit over 100 |
| `QuoteDefaultsRead` | Response form (adds `updated_at`) |
| `AppSettings` / `AppSettingsRead` | App configuration fields; `minimum_app_version` etc. validated with `VERSION_PATTERN` |
| `AppSettingsUpdate` | All-optional partial update |

### `platform/service.py`
| Function | What it does | Called by |
|---|---|---|
| `ensure_platform_settings(session)` | Get or create row 1 | `bootstrap.py` |
| `get_platform_settings(session)` | Get row 1 or `NotFoundError` | platform and admin routers, business service |
| `copy_quote_defaults(source, target)` | Copies every default field | `business.service.create_business` / `apply_platform_defaults`, `replace_quote_defaults` |
| `replace_quote_defaults(session, settings, payload)` | PUT semantics for defaults; logs `platform.defaults_updated` | `admin/router.py` |
| `update_app_settings(session, settings, payload)` | PATCH app settings; logs `platform.app_settings_updated` | `admin/router.py` |

### `platform/router.py`
`GET /v1/app-config` → `get_app_config` returns `AppSettingsRead`: what the
mobile app reads on launch (support contacts, legal links, version gate,
maintenance banner).

---

## 10. `app/business` — business profile

### `business/models.py`
**`BusinessProfile(QuoteDefaultsMixin, TimestampMixin, Base)`** — `business_name`,
`owner_name`, `phone`, `email`, `address`, `instagram`, `website`,
`tax_registration_number`, `payment_link`, `logo_path`, `quote_prefix` (`Q`),
`invoice_prefix` (`INV`), `next_quote_number`, `next_invoice_number` plus all
default fields from the mixin.

### `business/schemas.py`
| Name | Purpose |
|---|---|
| `PREFIX_PATTERN` | Allowed number prefixes (letters/digits, short) |
| `LOGO_URL` | Public path of the logo endpoint |
| `BusinessRead(QuoteDefaults)` | Response; `logo_path` is excluded, computed field `logo_url` is `/v1/business/logo` when a logo exists |
| `BusinessUpdate` | All-optional PATCH body (contact, numbering prefixes, defaults) |
| `REQUIRED_FIELDS` | Fields that cannot be set to `null` |

### `business/service.py`
| Function | What it does | Called by |
|---|---|---|
| `create_business(session, payload)` | New studio from first-launch setup; copies platform defaults onto omitted fields | `business/router.py` |
| `get_business(session, business_id)` | Load that studio or `NotFoundError` | `business/dependencies.py` |
| `list_businesses(session, *, limit, offset)` | Newest first | `admin/router.py` |
| `update_business(session, business, payload)` | Apply PATCH fields, reject `null` for required fields, `_ensure_valid_deposit`, log `business.updated` | `business/router.py` |
| `apply_platform_defaults(session, business, settings)` | Copy platform defaults onto the business, log `platform.defaults_applied` | `admin/router.py` |
| `save_logo(session, business, *, content_type, data, media_dir, max_bytes)` | `_validate_logo` (size → 413, type + magic bytes → 415), writes `<media_dir>/logos/logo-<uuid>.<ext>`, deletes the old file, logs | `business/router.py` |
| `remove_logo(session, business, media_dir)` | Deletes file and clears `logo_path`, logs | `business/router.py` |
| `resolve_logo_path(business, media_dir)` | Absolute path if the file exists, else `None` | `business/router.py`, `documents/service.py` |
| `allocate_quote_number(business)` | Returns `f"{quote_prefix}-{n:04d}"` (e.g. `Q-0001`) and increments the counter in the same transaction | `quotes/service.py` |
| `allocate_invoice_number(business)` | Same for invoices (`INV-0001`) | `invoices/service.py` |
| `_has_image_signature`, `_delete_media_file` | Helpers | internal |

### `business/dependencies.py`
- **`get_current_business(session, user, x_business_id)`** →
  `resolve_business` for the signed-in user (`X-Business-Id` optional
  when they have one studio).
- **`CurrentBusiness`** — `Annotated[BusinessProfile, Depends(...)]`.

Every feature router declares `business: CurrentBusiness` and passes it to its
service, and every service query filters on `business.id`. Login later only
changes this one function.

### `business/router.py`
| Endpoint | Function | Service call |
|---|---|---|
| `POST /v1/businesses` | `create_business_profile` | `create_business` |
| `GET /v1/business` | `get_business_profile` | — (dependency already loaded it) |
| `PATCH /v1/business` | `update_business_profile` | `update_business` |
| `PUT /v1/business/logo` | `upload_logo` (multipart `file`) | `save_logo` |
| `GET /v1/business/logo` | `download_logo` → `FileResponse` | `resolve_logo_path` |
| `DELETE /v1/business/logo` | `delete_logo` (204) | `remove_logo` |

---

## 11. `app/library` — saved items

Saved hair products, services, materials and fees that fill in quote lines.

### `library/rules.py`
Pure rules about which pricing fields belong to which kind:

| Name | Meaning |
|---|---|
| `KIND_FIELDS` | Fields allowed per kind (hair: `grams_per_pack`, `pack_price`, `markup_percent`; labour: `hourly_rate`; service/material/fee: `unit_price`, `unit_cost`, `unit_label`) |
| `REQUIRED_KIND_FIELDS` | Must be present (hair: `grams_per_pack` + `pack_price`; service/material/fee: `unit_price`; labour: none, it falls back to the business hourly rate) |
| `PRICING_FIELDS` | Union of all kind fields |
| `missing_fields(kind, values)` | Required fields that are `None` |
| `unrelated_fields(kind)` | Fields that must be cleared for that kind |

Used by `library/schemas.py` (create validation) and `library/service.py`
(update validation, clearing unrelated fields).

### `library/models.py`
**`LibraryItem`** — `business_id`, `kind`, `name`, `description`, `category`,
`taxable`, `is_archived`, and the pricing fields `grams_per_pack`,
`pack_price`, `markup_percent` (hair), `hourly_rate` (labour), `unit_price`,
`unit_cost`, `unit_label` (service, material, fee). Pricing fields that do
not belong to the item's kind are always `null`.

### `library/schemas.py`
- **`KIND_HELP`** — description text for the `kind` field.
- **`LibraryItemFields`** — shared fields.
- **`LibraryItemCreate`** — `_check_kind_fields` uses `rules.missing_fields`.
- **`LibraryItemUpdate`** — partial update.
- **`LibraryItemRead`** — response; computed `cost_per_gram` for hair
  (`round_rate(pack_price / grams_per_pack)`).

### `library/service.py`
| Function | What it does | Called by |
|---|---|---|
| `list_items(session, business, *, kind, search, include_archived, limit, offset)` | Filtered, paginated list ordered by kind, then name | `library/router.py` |
| `get_item(session, business, item_id)` | One item or `NotFoundError` | `library/router.py` |
| `get_items_by_id(session, business, item_ids)` | `{id: item}` in **one query**; raises `NotFoundError` naming unknown IDs | `quotes/line_resolver.py` |
| `create_item` / `update_item` / `delete_item` | Writes + activity log; update re-checks required fields and calls `_clear_unrelated_fields` | `library/router.py` |
| `count_items_by_kind(session, business)` | `{kind: count}` with zeros filled | `admin/service.py` |

Deleting an item does not break quotes: `quote_lines.library_item_id` is
`ON DELETE SET NULL` and each line stores its own copy of every value.

### `library/router.py`
`GET/POST /v1/library`, `GET/PATCH/DELETE /v1/library/{item_id}`.

---

## 12. `app/quotes` — quotes

### `quotes/policy.py`
Pure lifecycle rules.

- **`QuoteStatus`** — `draft`, `sent`, `accepted`, `declined`, `invoiced`.
- **`ALLOWED_TRANSITIONS`** — map of status → statuses it may move to by
  `PATCH /status`. `invoiced` maps to nothing (only invoice deletion unlocks it).
- **`INVOICEABLE_STATUSES`** — `draft`, `sent`, `accepted`.
- **`can_transition(current, target)`**, **`is_editable(status)`** (not
  invoiced), **`can_be_invoiced(status)`**.

Used by `quotes/service.py`, `invoices/service.py`, `dashboard/service.py`
and schemas for the status enum.

### `quotes/models.py`
- **`Quote`** — client fields, dates, notes, **snapshots** of `currency`,
  `tax_label`, `tax_rate_percent`, `deposit_mode`, `deposit_value`, and every
  total from `QuoteTotals`. Relationships: `lines` (ordered by `position`,
  `selectin` loaded, `delete-orphan`) and `invoice` (one-to-one).
- **`QuoteLine`** — `position`, `kind`, `description`, `taxable`, the input
  columns for its kind, and the results `price`, `cost`, `cost_per_gram`,
  `packs_needed`, `leftover_grams`.

Snapshots mean changing the business defaults never changes an existing
quote, and PDFs always reprint the same numbers.

### `quotes/schemas.py`
| Class | Role |
|---|---|
| `WORKED_EXAMPLE` | Request example used in `/docs` and the tests |
| `ClientDetails` | `name`, `phone`, `email` |
| `DepositInput` | `mode`, `value`; `_check_percent` rejects percent > 100 |
| `QuoteLineInput` | Optional `library_item_id`, `kind`, `description`, `taxable` and every pricing field; anything missing is resolved later |
| `QuoteCreate` | `client`, `title`, `lines` (≥ 1), dates, notes, optional `tax_rate_percent` / `deposit` overrides |
| `QuoteUpdate` | All optional; `lines`, `deposit` or `tax_rate_percent` trigger repricing |
| `QuotePreviewRequest` | `lines`, optional tax/deposit overrides |
| `QuoteStatusUpdate` | `status` |
| `PricedLineRead` / `QuoteLineRead` | Priced line in a preview / saved line (+ `id`, `position`) |
| `QuoteTotalsRead` | Mirror of `QuoteTotals` with field descriptions |
| `QuotePricingRead` | `currency`, `tax_label`, `tax_rate_percent`, `deposit`, `lines`, `totals` |
| `QuotePreviewRead` | Preview response |
| `QuoteRead.from_model(quote)` | Full quote response built from ORM |
| `QuoteSummary.from_model(quote)` | List row (number, status, client, total, profit…) |

### `quotes/line_resolver.py`
The bridge between request lines, library items, business defaults and the
pricing engine.

| Name | What it does |
|---|---|
| `DEFAULT_DESCRIPTIONS` | Fallback description per kind |
| `RESULT_FIELDS` | `LineResult` fields stored on a `QuoteLine` |
| `ResolvedLine` | `kind`, `description`, `library_item_id`, `pricing_input` |
| `resolve_lines(session, business, lines)` | Loads linked items with one query, then `_resolve_line` per line (1-based positions for error messages) |
| `resolve_saved_line(line)` | Rebuilds a `ResolvedLine` from a stored `QuoteLine` (duplicate, repricing without new lines) |
| `line_values(resolved, result)` | Dict of column values for a `QuoteLine` / `PricedLineRead` |
| `_resolve_line(...)` | Determines `kind` (line or item; mismatch → error), picks each value via `_first(line, item, default)`, `require`s mandatory ones (`"Line 2 (labour): \`hours\` is required."`) and builds the pricing input |
| `_item_value`, `_first`, `_stored` | Small helpers |

Business defaults used: `default_markup_percent`, `whole_packs_default`,
`hourly_rate`. Quantity defaults to 1 and unit cost to 0.

### `quotes/service.py`
| Function | What it does | Called by |
|---|---|---|
| `QuoteFilters` | `status`, `search`, `created_from`, `created_to` | router |
| `preview_quote(session, business, payload)` | Resolve + price, **no writes** | router |
| `list_quotes(session, business, filters, *, limit, offset)` | Search number/client/phone/title, date range, newest first, with total | router |
| `get_quote(session, business, quote_id)` | One quote or `NotFoundError` | quotes, invoices, documents routers/services |
| `create_quote(session, business, payload)` | Resolve, price, number, validity date, log, commit | router |
| `update_quote(session, business, quote, payload)` | `_ensure_editable`; plain fields copied; reprices when lines/deposit/tax change (reusing saved lines if `lines` was not sent) | router |
| `change_quote_status(session, quote, target)` | `can_transition` or `ConflictError`; stamps `sent_at`/`accepted_at` | router |
| `duplicate_quote(session, business, source)` | New draft with new number, same lines and pricing settings | router |
| `delete_quote(session, quote)` | Refuses if an invoice exists | router |
| `start_of_day(day)` | Midnight UTC, for date filters | `list_quotes`, `dashboard/service.py` |
| `_apply_pricing`, `_price`, `_business_deposit`, `_set_client`, `_ensure_editable`, `_first_set` | Internal helpers; `_apply_pricing` replaces the lines and copies every total onto the quote | internal |

### `quotes/router.py`
| Endpoint | Function |
|---|---|
| `POST /v1/quotes/preview` | `preview_quote_pricing` |
| `GET /v1/quotes` (`status`, `search`, `created_from`, `created_to`, pagination) | `list_all_quotes` |
| `POST /v1/quotes` (201, `Location`) | `create_new_quote` |
| `GET /v1/quotes/{quote_id}` | `get_single_quote` |
| `PATCH /v1/quotes/{quote_id}` | `update_existing_quote` |
| `DELETE /v1/quotes/{quote_id}` (204) | `delete_existing_quote` |
| `PATCH /v1/quotes/{quote_id}/status` | `update_quote_status` |
| `POST /v1/quotes/{quote_id}/duplicate` (201) | `duplicate_existing_quote` |

---

## 13. `app/invoices` — invoices

### `invoices/policy.py`
- **`InvoiceStatus`** — `unpaid`, `deposit_paid`, `paid`.
- **`amount_paid_for(status, *, total, deposit_amount)`** — 0, the deposit,
  or the total. The status is the single source of truth for `amount_paid`.

### `invoices/models.py`
**`Invoice`** — `business_id`, `quote_id` (**unique**, `ON DELETE RESTRICT`:
one invoice per quote, and a quote with an invoice cannot be deleted),
`number`, `status`, `issue_date`, `due_date`, snapshot `currency`,
`subtotal`, `tax_amount`, `total`, `deposit_amount`, `amount_paid`,
`payment_link`, `notes`, `terms`, `paid_at`; relationship `quote`.

### `invoices/schemas.py`
- **`InvoiceCreate`** — optional `issue_date`, `due_date`, `notes`.
- **`InvoiceStatusUpdate`** — `status`.
- **`InvoiceSummary.from_model`** — list row incl. quote number, client name
  and computed `amount_due = total − amount_paid`.
- **`InvoiceRead.from_model`** — full invoice incl. the quote's lines
  (reusing `QuoteLineRead`).

### `invoices/service.py`
| Function | What it does |
|---|---|
| `create_invoice(session, business, quote, payload)` | Rejects a second invoice and non-invoiceable statuses (409); dates default to today + `invoice_due_days`; due before issue → 422; copies totals from the quote, takes `payment_link` and `invoice_terms` from the business; **sets the quote to `invoiced`**; logs; commits |
| `list_invoices(session, business, *, status, search, limit, offset)` | Joins quotes to search invoice number, quote number, client name |
| `get_invoice(session, business, invoice_id)` | One or `NotFoundError` |
| `change_invoice_status(session, invoice, target)` | Recomputes `amount_paid`, sets/clears `paid_at`, logs |
| `delete_invoice(session, invoice)` | Moves the quote back to `accepted`, logs, deletes |

### `invoices/router.py`
`POST /v1/quotes/{quote_id}/invoice` (uses `quotes.service.get_quote`),
`GET /v1/invoices`, `GET /v1/invoices/{invoice_id}`,
`PATCH /v1/invoices/{invoice_id}/status`, `DELETE /v1/invoices/{invoice_id}`.

---

## 14. `app/documents` — PDFs

The PDF pipeline has three independent stages, so layout and content can be
changed separately:

```text
records (Quote / Invoice / BusinessProfile)
   │  builders.py        decide WHAT to print (all text already formatted)
   ▼
DocumentData             plain frozen dataclasses, no ORM, no ReportLab
   │  renderer.py        decide HOW it looks (ReportLab platypus)
   ▼
PDF bytes                returned by service.py → router.py as application/pdf
```

### `documents/data.py`
| Class | Fields |
|---|---|
| `BusinessBlock` | `name`, `contact_lines`, `logo_path` |
| `LabeledValue` | `label`, `value`, `emphasis` |
| `LineTable` | `headers`, `rows`, `column_widths` (fractions of the page width), `numeric_columns` (right-aligned) |
| `TextSection` | `heading`, `body` |
| `DocumentData` | `title`, `number`, `business`, `meta`, `client_heading`, `client_lines`, `table`, `amounts`, `highlights`, `badge`, `payment_link`, `payment_label`, `sections` |

### `documents/formatting.py`
`money(value, currency=None)` → `"AED 2,104.00"`; `quantity(value)` drops
trailing zeros (`3.5`); `times(count, rate)` → `"3.5 h × 180.00"`;
`percent(value)` → `"61.85%"`; `long_date(value)` → `"15 Oct 2026"`.
`MULTIPLICATION_SIGN` is the `×` character.

### `documents/theme.py`
Brand colours from the Figma design (`BERRY`, `BERRY_DARK`, `BERRY_TINT`,
`BERRY_WASH`, `INK*`, `GOLD*`), `FontSet` (serif, regular, bold),
`BRAND_FONTS` (DM Serif Display + Plus Jakarta Sans, bundled in
`documents/fonts/` with their OFL licences), `FALLBACK_FONTS` (built-in
Times/Helvetica) and `load_fonts()` which registers the TTFs once and falls
back if they cannot be loaded.

### `documents/builders.py`
| Function | Produces |
|---|---|
| `build_quote_document(business, quote, logo_path)` | Client quote: date/valid until/appointment, client block, lines (description, details, amount), subtotal/tax/total/deposit/balance, deposit payment link, notes and terms |
| `build_invoice_document(business, invoice, logo_path)` | Invoice: status badge (`INVOICE_BADGES`), issue/due dates, quote reference, lines, totals, paid to date, **amount due**, payment link, notes, terms |
| `build_cost_sheet_document(business, quote, logo_path)` | Internal sheet ("INTERNAL – DO NOT SHARE"): highlight cards (revenue, cost, profit, profit/hour, margin), per-line breakdown with cost/price/profit, totals and labour hours |
| `_business_block`, `_client_lines`, `_client_table`, `_client_detail`, `_cost_breakdown`, `_labour_rate`, `_unit_rate`, `_hair_breakdown`, `_tax_row`, `_sections` | Helpers; `_hair_breakdown` prints e.g. "170 g needed, 2 packs × 350.00, +60%, 30 g left over" |

### `documents/renderer.py`
**`render_document(document) -> bytes`** builds an A4 `SimpleDocTemplate`
with: `_header` (logo or business name, contact lines, title, number, badge,
`_meta_table`), `_client_block`, optional `_highlight_cards`, `_line_table`,
`_amounts_table` (kept together on one page), `_payment_block`, text
sections, and `_footer` (business · document number, page number) drawn on
every page. `_Styles` holds the paragraph styles for a `FontSet`. `_text` and
`_multiline` escape user text so names like `A&B <Studio>` cannot break the
markup. `_logo` scales the logo to fit `LOGO_MAX_WIDTH × LOGO_MAX_HEIGHT`.

### `documents/service.py`
- **`RenderedDocument`** — `filename`, `content`.
- **`render_quote_pdf` / `render_cost_sheet_pdf`** — `quotes.service.get_quote`
  → builder → renderer. Filenames `Q-0001.pdf`, `Q-0001-cost-sheet.pdf`.
- **`render_invoice_pdf`** — `invoices.service.get_invoice` → builder →
  renderer. Filename `INV-0001.pdf`.

All three use `business.service.resolve_logo_path` for the logo.

### `documents/router.py`
`GET /v1/quotes/{quote_id}/pdf`, `GET /v1/quotes/{quote_id}/cost-sheet/pdf`,
`GET /v1/invoices/{invoice_id}/pdf`. `DownloadParam` (`?download=true`) picks
`Content-Disposition: attachment` instead of `inline`; `_pdf_response` builds
the `Response`. `PDF_RESPONSE` documents the binary response in OpenAPI.

---

## 15. `app/dashboard` — figures

### `dashboard/schemas.py`
- **`PeriodMetrics`** — `date_from`, `date_to`, `quotes_created`,
  `quoted_value`, `quotes_won`, `win_rate_percent`, `invoices_issued`,
  `invoiced_value`, `collected`, `profit`, `labour_hours`, `profit_per_hour`.
- **`OutstandingRead`** — `unpaid_invoices`, `amount_due`.
- **`DashboardRead`** — `currency`, `period`, `outstanding`,
  `quote_status_counts`, `invoice_status_counts`, `recent_quotes`
  (`QuoteSummary`).

### `dashboard/service.py`
All figures are SQL aggregates; because money is stored as scaled integers
the sums are exact.

| Function | What it computes |
|---|---|
| `get_dashboard(session, business, *, date_from, date_to)` | Defaults to the current month so far; assembles everything below plus the 5 most recent quotes |
| `compute_period_metrics(...)` | Quotes **created** in the period (count, value, won = accepted or invoiced, win rate); invoices **issued** in the period (count, value, collected, profit and labour hours of their quotes, profit per hour) |
| `compute_outstanding(session, business)` | Unpaid + deposit-paid invoices and `total − amount_paid` |
| `count_quotes_by_status`, `count_invoices_by_status` | Every status present, zeros included |
| `_sum(column)` | `coalesce(sum(column), 0)` typed as the column, so results come back as `Decimal` |

`WON_STATUSES`, `RECENT_QUOTES_LIMIT` are module constants. Used by
`dashboard/router.py` (`GET /v1/dashboard`, rejects `date_from > date_to`)
and `admin/service.py`.

---

## 16. `app/admin` — owner dashboard

Endpoints for the owner's web dashboard. The admin service has **no queries
of its own**; it composes the other features' services.

### `admin/schemas.py`
- **`BusinessSnapshot`** — `id`, `business_name`, `currency`, `has_logo`,
  `created_at`.
- **`AdminOverview`** — `business` snapshot, `this_month` and `all_time`
  `PeriodMetrics`, `outstanding`, quote and invoice status counts,
  `library_item_counts` per kind, `recent_activity`.
- **`AdminBusinessDetail`** — `profile` (full `BusinessRead`), `usage`
  (all-time `PeriodMetrics`), `outstanding`, `library_item_counts`.

### `admin/service.py`
- **`get_overview(session, business)`** — uses
  `dashboard.service.compute_period_metrics` / `compute_outstanding` /
  `count_*_by_status`, `library.service.count_items_by_kind` and
  `activity.service.list_activity` (`RECENT_ACTIVITY_LIMIT`).
- **`get_business_detail(session, business)`**.

### `admin/router.py`
| Endpoint | Function | Calls |
|---|---|---|
| `GET /v1/admin/overview` | `get_admin_overview` | `admin.service.get_overview` |
| `GET /v1/admin/business` | `get_admin_business` | `admin.service.get_business_detail` |
| `GET /v1/admin/defaults` | `get_quote_defaults` | `platform.service.get_platform_settings` |
| `PUT /v1/admin/defaults` | `replace_platform_quote_defaults` | `platform.service.replace_quote_defaults` |
| `POST /v1/admin/defaults/apply` | `apply_defaults_to_business` | `business.service.apply_platform_defaults` |
| `GET /v1/admin/settings` | `get_platform_app_settings` | `platform.service.get_platform_settings` |
| `PATCH /v1/admin/settings` | `update_platform_app_settings` | `platform.service.update_app_settings` |
| `GET /v1/admin/activity` | `list_admin_activity` | `activity.service.list_activity` |

Changing platform defaults affects **new** businesses only; existing
businesses pick them up through `POST /v1/admin/defaults/apply`. Existing
quotes never change (they hold snapshots).

---

## 17. `migrations` — Alembic

| File | Purpose |
|---|---|
| `alembic.ini` | `script_location = migrations`, file names `YYYYMMDD_<rev>_<slug>.py` |
| `migrations/env.py` | `DATABASE_URL` from `core.config.get_settings()` (so `PTP_DATABASE_URL` works); `target_metadata = app.db.registry.Base.metadata`; `render_as_batch=True` (SQLite `ALTER` support); `render_item` writes `ScaledDecimal` as `sa.Integer` and `UTCDateTime` as `sa.DateTime` so migrations do not import app types; `run_migrations_offline` / `run_migrations_online` |
| `migrations/script.py.mako` | Template for new revisions |
| `migrations/versions/20261015_0001_initial_schema.py` | Revision `0001`: all seven tables, indexes and constraints |
| `migrations/versions/20261017_0002_multi_business.py` | Revision `0002`: `tagline`, activity `business_id`, quote/invoice numbers unique per business |
| `migrations/versions/20261017_0003_auth.py` | Revision `0003`: `users`, `auth_sessions`, `business_profiles.user_id` |

---

## 18. `tests`

| File | Covers |
|---|---|
| `tests/conftest.py` | `app` (in-memory SQLite, temp media folder, small logo limit, `create_all`), `client` (`TestClient` that creates a business and sends `X-Business-Id`), `quote_payload` (deep copy of `WORKED_EXAMPLE`), `created_quote` |
| `tests/unit/test_pricing.py` | Every pricing function: packs and leftovers, per-gram mode, markup, labour, items, tax on taxable lines only, deposits and caps, rounding, worked example, error cases |
| `tests/unit/test_policies.py` | Quote transition table, editability, invoiceability; `amount_paid_for` |
| `tests/api/test_business_and_config.py` | Health, app config, business PATCH, numbering, logo upload/download/delete incl. 413/415 |
| `tests/api/test_library.py` | CRUD, kind validation, filters, archive |
| `tests/api/test_quotes.py` | Preview = saved pricing, library and default resolution, line errors, update/reprice, status flow, duplicate, search/date filters, delete rules |
| `tests/api/test_invoices_and_documents.py` | Invoice creation rules, locking, payments, deletion unlocking, PDFs (content type, filename, `download`) |
| `tests/api/test_dashboard_and_admin.py` | Period metrics, outstanding, counts, admin overview, defaults replace/apply, app settings, activity |

---

## 19. End-to-end data flows

### 19.1 Start-up

```text
uvicorn → app.main.app = create_app()
  → build_engine / build_session_factory → app.state
  → lifespan: media_dir.mkdir
            → bootstrap.seed_required_rows
                → platform.ensure_platform_settings   (row 1, defaults + app config)
                → commit
            (businesses are created by POST /v1/businesses)
```

### 19.2 Live pricing while the stylist types

```text
POST /v1/quotes/preview  {lines, deposit?, tax_rate_percent?}
  → quotes.service.preview_quote
      → line_resolver.resolve_lines → library.get_items_by_id (1 query)
      → pricing.price_quote
  ← QuotePreviewRead (nothing saved)
```

### 19.3 Quote → invoice → payment → PDF

```text
POST /v1/quotes                → Quote(draft, Q-0001) + lines + totals snapshot
PATCH /v1/quotes/1/status sent → sent_at
PATCH /v1/quotes/1/status accepted → accepted_at
POST /v1/quotes/1/invoice      → Invoice(unpaid, INV-0001) copies totals; quote → invoiced (locked)
PATCH /v1/invoices/1/status deposit_paid → amount_paid = deposit_amount
PATCH /v1/invoices/1/status paid         → amount_paid = total, paid_at
GET /v1/invoices/1/pdf         → documents.service → builders → renderer → bytes
GET /v1/dashboard              → SQL sums over quotes + invoices
```

Each write above also appends one `activity_logs` row in the same commit.

### 19.4 Where each default comes from

```text
Admin: PUT /v1/admin/defaults      → platform_settings row
Seed / apply defaults              → copy_quote_defaults → business_profiles row
Stylist: PATCH /v1/business        → business_profiles row
Create quote                       → line value ▸ library item ▸ business default
                                     tax/deposit: request ▸ business
                                     → snapshot on quotes row (never changes later)
Create invoice                     → totals from quote; terms + payment link from business
```

---

## 20. Database schema

| Table | Key columns | Relationships |
|---|---|---|
| `platform_settings` | `id = 1`, quote defaults, app config | — |
| `business_profiles` | `id = 1`, contact, branding, defaults, number counters | — |
| `library_items` | `business_id`, `kind`, `name`, pricing fields, `is_archived` | → `business_profiles` (CASCADE) |
| `quotes` | `business_id`, `number` (unique), `status`, client, snapshots, totals | → `business_profiles` (CASCADE) |
| `quote_lines` | `quote_id`, `position`, `kind`, inputs, results | → `quotes` (CASCADE), → `library_items` (SET NULL) |
| `invoices` | `business_id`, `quote_id` (unique), `number` (unique), `status`, totals, `amount_paid` | → `business_profiles` (CASCADE), → `quotes` (RESTRICT) |
| `activity_logs` | `action`, `entity_type`, `entity_id`, `summary`, `created_at` | — |

Money columns are `INTEGER` (scaled by 100, or 10,000 for `cost_per_gram`);
timestamps are UTC. Foreign keys are enforced on every SQLite connection.
