# Build Guide

How this backend was built, **in order**, and how each piece plugs into the
ones before it. Follow it to rebuild the project from an empty folder, to
onboard onto the codebase, or as a recipe for adding the next feature.

- For setup and the API summary see the [README](../README.md).
- For a file-by-file lookup see the [Technical Reference](TECHNICAL_REFERENCE.md).

## The guiding idea

Build **from the inside out**: first the parts that depend on nothing (the
pricing maths), then the plumbing every feature needs (config, database,
errors), then features in the order they depend on each other, and only then
the things that read across features (PDFs, dashboard, admin).

```text
Step  0  Decisions
Step  1  Project scaffolding                      pyproject, ruff, folders
Step  2  Core primitives                          config, clock, errors
Step  3  Database layer                           types, base, session
Step  4  Pricing engine  ← tested first           pure Python
Step  5  The runnable app                         schemas, handlers, deps, OpenAPI, factory, health
Step  6  Activity log                             used by every write below
Step  7  Platform settings                        admin defaults + app config
Step  8  Business profile + CurrentBusiness       owner of all data, numbering, logo
Step  9  Library                                  saved items
Step 10  Quotes                                   policy → models → schemas → resolver → service → router
Step 11  Invoices                                 built on quotes
Step 12  PDF documents                            reads quotes, invoices, business
Step 13  Dashboard                                SQL over quotes + invoices
Step 14  Admin                                    composes everything
Step 15  Migrations                               Alembic from the final models
Step 16  API tests and the quality loop
Step 17  Documentation
```

Each step ends with **"Connects to"** (what it plugs into) and **"Check"**
(how we confirmed it works before moving on).

---

## Step 0 — Decisions

Made before writing code, from the product design:

| Decision | Choice | Why |
|---|---|---|
| Framework | FastAPI + Pydantic v2 | Typed requests, automatic OpenAPI docs |
| Database | SQLite via SQLAlchemy 2 (sync) + Alembic | Zero setup now; switching to Postgres later is a URL change plus a migration |
| Money | `Decimal` end to end, stored as scaled integers | Exact totals and exact SQL sums; floats are never used |
| PDFs | ReportLab | Pure Python, no system dependencies |
| Auth | Email + name + password, OTP, then login issues the token | Email delivery of OTP later |
| Structure | Feature folders (`router`/`schemas`/`service`/`models`) | Follows the reference architecture repository; a feature can be read in one folder |
| Style | PEP 8 enforced by Ruff, Python 3.12 idioms | One consistent codebase |

---

## Step 1 — Project scaffolding

**Files:** `pyproject.toml`, `.gitignore`, `.env.example`, empty `app/`,
`tests/`, `migrations/` packages.

1. Create a Python 3.12 virtual environment in `.venv`.
2. `pyproject.toml` declares:
   - runtime dependencies: `fastapi`, `uvicorn[standard]`, `pydantic`,
     `pydantic-settings`, `sqlalchemy`, `alembic`, `python-multipart` (logo
     uploads), `email-validator` (`EmailStr`), `reportlab`;
   - a `dev` extra: `pytest`, `httpx2` (used by Starlette's `TestClient`),
     `ruff`;
   - package data so the PDF fonts ship with the package;
   - Ruff: line length 88, target `py312`, rules `E W F I N UP B SIM C4 RUF`.
3. `pip install -e ".[dev]"`.

**Connects to:** everything; Ruff and pytest run against every later step.
**Check:** `ruff check app` and `python -c "import app"` both succeed.

---

## Step 2 — Core primitives (`app/core`)

These have **no dependencies on features**, so they come first.

1. **`core/config.py`** — `Settings` (pydantic-settings, `PTP_` prefix) and
   the cached `get_settings()`. Every tunable value lives here: database URL,
   media folder, logo size limit, CORS origins.
2. **`core/clock.py`** — `utc_now()` and `today()`. Every timestamp in the
   app goes through these, so all times are timezone-aware UTC.
3. **`core/errors.py`** — `ApplicationError` and its subclasses
   (`NotFoundError`, `ConflictError`, `BusinessRuleError`,
   `FileTooLargeError`, `UnsupportedFileTypeError`). They deliberately do
   **not** import FastAPI: services raise domain errors, and only the web
   layer decides HTTP status codes.

**Connects to:** config → factory, dependencies and migrations; clock → models
and services; errors → every service and (in Step 5) the error handlers.

---

## Step 3 — Database layer (`app/db`)

1. **`db/types.py`** — the column types the whole schema relies on:
   - `ScaledDecimal(scale)` stores money as integers (`2104.00` → `210400`).
     SQLite has no exact decimal, and integer sums are exact.
   - `UTCDateTime` stores naive UTC and returns aware datetimes.
   - `str_enum()` stores enum **values** as strings.
2. **`db/base.py`** — `Base` with a constraint **naming convention** (Alembic
   needs stable names to alter SQLite tables) and `TimestampMixin`
   (`created_at`, `updated_at` from `clock.utc_now`).
3. **`db/session.py`** — `build_engine` (SQLite thread setting, `StaticPool`
   for in-memory test databases, `PRAGMA foreign_keys=ON` on every
   connection) and `build_session_factory` (`expire_on_commit=False` so the
   router can read objects after the service commits).

There are no models yet; each feature adds its own and `db/registry.py`
(Step 15) collects them.

**Connects to:** every `models.py` uses `Base`, `TimestampMixin` and the types;
`factory.py` and `migrations/env.py` use `session.py`.

---

## Step 4 — Pricing engine (`app/pricing`) — tested first

The heart of the product, so it is written as **pure Python with no imports
from FastAPI, SQLAlchemy or any feature**, and fully unit-tested before
any endpoint exists.

1. **`pricing/enums.py`** — `LineKind` (hair, labour, service, material, fee)
   and `DepositMode` (percent, fixed): the shared vocabulary.
2. **`pricing/errors.py`** — `PricingError`.
3. **`pricing/money.py`** — `round_money` (half-up, 2 dp), `round_rate`
   (4 dp), `percent_of`, constants.
4. **`pricing/calculator.py`**
   - Inputs as frozen dataclasses: `HairLine`, `LabourLine`, `ItemLine`
     (the `LineInput` union) and `Deposit`.
   - Outputs: `LineResult`, `QuoteTotals`, `PricedQuote`.
   - `price_hair` / `price_labour` / `price_item`, dispatched by
     `price_line` with `match`.
   - `calculate_deposit`, `calculate_totals`, `price_quote`.
   - **Rounding rule:** round every line, then sum the rounded lines, so the
     printed columns always add up.
5. **`tests/unit/test_pricing.py`** — packs and leftovers, per-gram mode,
   markup, labour, items, tax on taxable lines only, deposits and the cap,
   rounding edge cases, invalid input, and the **worked example**
   (total 2,104.00, profit 1,240.00).

**Connects to:** `quotes/line_resolver.py` builds the inputs and
`quotes/service.py` calls `price_quote` (Step 10). `pricing.money` is also
reused for input rounding (Step 5) and invoice amounts (Step 11).
**Check:** `pytest tests/unit/test_pricing.py`.

---

## Step 5 — The runnable app

Now we build the web plumbing every feature will plug into, and start the app
with only health checks.

1. **`core/schemas.py`** — reusable field types (`Money`, `Percent`,
   `MarkupPercent`, `Grams`, `Hours`, `Quantity`, `HttpLink`), all passed
   through `TwoDecimals` (rounds input with `pricing.money.round_money`), the
   error envelope models, generic `Page[ItemT]` and `error_responses()` so
   each route documents its errors.
2. **`core/handlers.py`** — `register_exception_handlers`: `ApplicationError`
   subclasses → 404/409/413/415/422, `PricingError` → 422 `pricing_error`,
   `RequestValidationError` → 422 `validation_error` with per-field details.
   All responses use `{"error": {"code", "message", "details"}}`.
3. **`core/dependencies.py`** — `get_session` (from
   `app.state.session_factory`), `get_app_settings` (from `app.state`),
   `get_pagination`; exposed as `SessionDep`, `SettingsDep`, `PaginationDep`.
4. **`core/openapi.py`** — the long API description, the ordered tags with
   descriptions, and `operation_id` (function name → `operationId`).
5. **`app/health.py`** — `/health/live` and `/health/ready`.
6. **`app/factory.py`** — `create_app(settings)`: engine + session factory on
   `app.state`, lifespan, FastAPI metadata and Swagger options, CORS, error
   handlers, routers.
7. **`app/main.py`** — `app = create_app()`.

**Why a factory:** tests call `create_app(Settings(database_url="sqlite:///:memory:"))`
and get a fully isolated app. Nothing reads global state at import time.
**Check:** `uvicorn app.main:app --reload`, open `/docs`, call `/health/ready`.

---

## Step 6 — Activity log (`app/activity`)

Built before any feature that writes, because every write records one.

1. `enums.py` — `ActivityAction` values named `<entity>.<verb>`.
2. `models.py` — `ActivityLog`.
3. `schemas.py` — `ActivityRead`.
4. `service.py`
   - `record_activity(...)` only **adds** the row and does not commit. The
     calling service commits once, so a change and its log entry are saved
     together or not at all.
   - `list_activity(...)` reads it back.

**Connects to:** called by the platform, business, library, quotes and
invoices services. Read by admin (Step 14).

---

## Step 7 — Platform settings (`app/platform`)

The admin-owned row (`id = 1`) with **quote defaults** and **mobile app
configuration**.

1. `models.py`
   - `QuoteDefaultsMixin` holds the default columns: currency, tax label and
     rate, hourly rate, markup, deposit, whole packs, validity and due days,
     and terms.
   - `PlatformSettings` combines that mixin with the app config fields.
   - The mixin is written once here and reused by the business profile in
     Step 8.
2. `schemas.py`: `QuoteDefaults` (with deposit validation), `AppSettings*`.
3. `service.py`
   - `ensure_platform_settings` creates the row on first run.
   - `get_platform_settings` reads it.
   - `copy_quote_defaults` copies the default fields onto any object that
     has them.
   - `replace_quote_defaults` and `update_app_settings` change the row; both
     log the change.
4. `router.py` — `GET /v1/app-config` for the mobile app.

**Connects to:**
- `bootstrap.py` seeds the row.
- `business.service` copies the defaults into a new business.
- Admin edits both parts (Step 14).

---

## Step 8 — Business profile (`app/business`) and request scoping

The business owns every quote, invoice and library item, so it comes before
them.

1. `models.py` — `BusinessProfile(QuoteDefaultsMixin, …)` adds:
   - contact and branding fields, including the logo path and payment link;
   - number prefixes and counters.
2. `schemas.py`
   - `BusinessRead` hides the file path and exposes a computed `logo_url`.
   - `BusinessUpdate` is the PATCH body.
3. `service.py`
   - Profile:
     - `create_business` creates a studio from first-launch setup.
     - `get_business` loads one by id.
     - `update_business` applies a PATCH, rejects `null` for required
       fields and validates the deposit.
     - `apply_platform_defaults` copies the platform defaults onto it.
   - Logo:
     - `save_logo` checks the size, the content type and the image's magic
       bytes, then writes the file under `media/logos/`.
     - `remove_logo` deletes it; `resolve_logo_path` finds it on disk.
   - Numbering:
     - `allocate_quote_number` and `allocate_invoice_number` return
       `Q-0001` and `INV-0001`, incrementing the counter in the caller's
       transaction.
4. **`dependencies.py`**
   - `CurrentBusiness` answers "which business is this request for?"
   - It uses the signed-in user and optional `X-Business-Id`. Every later
     router depends on it, and every later service filters by `business.id`.
5. **`app/bootstrap.py`** — `seed_required_rows` seeds the platform row, then
   the business, and is called from the lifespan in `factory.py`. It lives
   above both features so `platform` never imports `business`.
6. `router.py` — `POST /v1/businesses`, `GET/PATCH /v1/business`,
   `PUT/GET/DELETE /v1/business/logo`.
7. `app/api.py` — the `/v1` router; each feature's router is added here as
   it is built.

**Connects to:**
- Every later feature takes `CurrentBusiness`.
- Quotes and invoices allocate their numbers here.
- PDFs use the logo and contact details.
- Quote lines fall back to the business defaults.

**Check:** `POST /v1/businesses` → `PATCH /v1/business` with `X-Business-Id`;
upload a logo.

---

## Step 9 — Library (`app/library`)

Saved items the stylist picks from when quoting.

1. **`rules.py`** (pure)
   - `KIND_FIELDS` and `REQUIRED_KIND_FIELDS` define which pricing fields
     belong to which kind.
   - `missing_fields` and `unrelated_fields` apply those rules.
2. `models.py` — `LibraryItem`, scoped by `business_id`.
3. `schemas.py`
   - Create, update and read models.
   - Create validates the kind's fields using `rules`.
   - Read adds a computed `cost_per_gram` for hair.
4. `service.py`
   - CRUD and search.
   - `get_items_by_id` loads many items in one query; quotes need this.
   - `count_items_by_kind` is used by admin.
   - Updates clear fields that do not belong to the item's kind.
5. `router.py` — `/v1/library` CRUD.

**Connects to:**
- `quotes/line_resolver.py` reads items to fill quote lines.
- Admin counts items.
- Quote lines keep their own copy of every value and use
  `ON DELETE SET NULL`, so deleting an item never changes an existing quote.

---

## Step 10 — Quotes (`app/quotes`)

The central feature, built in this inner order:

1. **`policy.py`** (pure)
   - `QuoteStatus`, `ALLOWED_TRANSITIONS`, `can_transition`, `is_editable`,
     `can_be_invoiced`.
   - Unit-tested in `tests/unit/test_policies.py`.
2. **`models.py`**
   - `Quote` stores the client details.
   - It also stores **snapshots** of the currency, tax and deposit
     settings, and every total.
   - `QuoteLine` stores each line's inputs and its priced results.
   - Snapshots mean editing the business later never changes an old quote
     or its PDF.
3. **`schemas.py`**
   - Request bodies: `QuoteLineInput` (every field optional),
     `QuoteCreate`, `QuoteUpdate`, `QuotePreviewRequest`,
     `QuoteStatusUpdate`.
   - Response models: `QuoteRead`, `QuoteSummary`, `QuotePreviewRead`
     (built with `from_model`).
   - `WORKED_EXAMPLE` serves as both the `/docs` example and a test
     fixture.
4. **`line_resolver.py`** — the bridge between request lines, library items,
   business defaults and the pricing engine:
   - `resolve_lines` loads the linked items with one query.
   - It fills each value from, in order: the line, the library item, the
     business default.
   - Missing values raise "Line 2 (labour): `hours` is required."
   - The result is `ResolvedLine`s holding pure pricing inputs.
   - `resolve_saved_line` rebuilds inputs from stored lines (for duplicate
     and partial reprice).
   - `line_values` maps a priced line back to columns.
5. **`service.py`** — the use cases. Each write commits **once**, with its
   activity entry.
   - `preview_quote` prices without saving.
   - `create_quote` resolves, prices, allocates a number and snapshots.
   - `update_quote` refuses invoiced quotes. It reprices only when lines,
     deposit or tax change; if lines were not sent, it reuses the saved
     lines.
   - `change_quote_status` checks the transition table and stamps
     `sent_at` / `accepted_at`.
   - `duplicate_quote` creates a new draft with a new number.
   - `delete_quote` is refused if the quote has an invoice.
   - `list_quotes` searches and filters by date range.
6. **`router.py`** — eight endpoints, each with a summary, description,
   examples and `error_responses(...)`.

**Connects to:**
- Pricing (Step 4), library (Step 9), business numbering and defaults
  (Step 8), activity (Step 6).
- Invoices, PDFs and the dashboard all read quotes next.

**Check:** `POST /v1/quotes/preview` with the worked example returns total
2,104.00 and profit 1,240.00. `POST /v1/quotes` returns the same numbers.

---

## Step 11 — Invoices (`app/invoices`)

1. **`policy.py`**
   - `InvoiceStatus`.
   - `amount_paid_for(status)` returns 0, the deposit or the total. The
     status alone decides `amount_paid`.
2. **`models.py`**
   - `Invoice.quote_id` is **unique** (one invoice per quote).
   - It is `ON DELETE RESTRICT`, so a quote with an invoice can't be
     deleted.
   - The invoice snapshots the quote's totals.
3. `schemas.py`
   - `InvoiceCreate` takes optional dates and notes.
   - `InvoiceRead` includes the quote's lines and computes `amount_due`.
4. `service.py`
   - `create_invoice`:
     - rejects a second invoice, and statuses that can't be invoiced;
     - defaults the due date to the issue date plus `invoice_due_days`;
     - copies the totals from the quote, and the payment link and terms
       from the business;
     - sets the quote to **`invoiced`**, which locks it.
   - `change_invoice_status` records payments.
   - `delete_invoice` moves the quote back to `accepted`.
5. `router.py`
   - `POST /v1/quotes/{id}/invoice` loads the quote through
     `quotes.service.get_quote`.
   - The `/v1/invoices` endpoints list, read, record payments and delete.

**Connects to:** quotes (reads them and locks them), business numbering.
Read by PDFs and the dashboard.

---

## Step 12 — PDF documents (`app/documents`)

Built after quotes and invoices because it only reads them. It has three
separate stages:

1. **`data.py`** — `DocumentData` and its parts. These are plain dataclasses
   of already-formatted text, with no ORM or ReportLab objects.
2. **`formatting.py`** — `money`, `quantity`, `times`, `percent`,
   `long_date`.
3. **`theme.py`**
   - Brand colours from the Figma design.
   - `load_fonts` registers the bundled DM Serif Display and Plus Jakarta
     Sans fonts (with their OFL licences), or falls back to built-in
     fonts.
4. **`builders.py`** — what each document says:
   - `build_quote_document` for the client quote;
   - `build_invoice_document` with a status badge and the amount due;
   - `build_cost_sheet_document`, the internal sheet with profit cards and
     a per-line cost breakdown.
5. **`renderer.py`**
   - `render_document` controls how the page looks: an A4 ReportLab layout
     with a header, client block, line table, amounts, payment link,
     sections and a footer on every page.
   - User text is escaped.
6. **`service.py`**
   - Loads the records with `get_quote` / `get_invoice` and builds the
     document data.
   - Renders it, and returns `RenderedDocument(filename, content)`.
7. **`router.py`** — three `GET …/pdf` endpoints; `?download=true` switches
   `Content-Disposition` from inline to attachment.

**Why the split:** wording changes touch only the builders, layout changes
touch only the renderer, and each can be tested on its own.
**Check:** render the worked example to PDF and inspect it: total 2,104.00 on
the quote, profit 1,240.00 on the cost sheet.

---

## Step 13 — Dashboard (`app/dashboard`)

1. `schemas.py` — `PeriodMetrics`, `OutstandingRead`, `DashboardRead`.
2. `service.py` — SQL aggregates, which stay exact because money is stored
   as scaled integers:
   - quotes created and won in a period;
   - invoices issued, money collected, profit and labour hours;
   - money outstanding and status counts.
   - `_sum` wraps `coalesce(sum(...), 0)`, so empty periods return `0.00`.
3. `router.py` — `GET /v1/dashboard`:
   - defaults to the current month;
   - rejects `date_from > date_to`.

**Connects to:** reads quotes and invoices; reused by admin.

---

## Step 14 — Admin (`app/admin`)

The last feature, because it **composes** the others and has no queries of
its own.

1. `schemas.py` — `AdminOverview`, `AdminBusinessDetail`, `BusinessSnapshot`.
2. `service.py` — `get_overview` and `get_business_detail` call the
   dashboard, library and activity services.
3. `router.py` — `/v1/admin/...` endpoints:
   - `overview` and `business` come from `admin.service`;
   - `defaults` and `settings` come from `platform.service`;
   - `defaults/apply` comes from `business.service`;
   - `activity` comes from `activity.service`.

**Connects to:** every earlier feature, through its service functions only.

---

## Step 15 — Migrations (`migrations/`)

Generated once the models were final.

1. **`app/db/registry.py`** imports every `models.py` so `Base.metadata` is
   complete.
2. `alembic.ini` + **`migrations/env.py`**:
   - The URL comes from `Settings`, so `PTP_DATABASE_URL` works.
   - The metadata comes from the registry.
   - `render_as_batch=True` enables SQLite `ALTER` support.
   - `render_item` writes custom types as plain `Integer` / `DateTime`.
3. `alembic revision --autogenerate -m "initial schema"` produced
   `20261015_0001_initial_schema.py`, then it was reviewed by hand.

**Check:**
- `alembic upgrade head` on an empty database.
- `alembic check` reports *"No new upgrade operations detected"*: the models
  and the migration match.

---

## Step 16 — API tests and the quality loop

1. **`tests/conftest.py`**
   - `app` is a new `create_app` with an in-memory database and a temporary
     media folder, with tables created from the registry.
   - `client` is a `TestClient`; it runs the lifespan, so seeding happens.
   - `quote_payload` / `created_quote` are built from `WORKED_EXAMPLE`.
2. **`tests/api/`** has one file per area. They test behaviour over HTTP: the
   status codes, the error envelope, the rules (locking, transitions,
   numbering), the PDFs, the dashboard sums and the admin flows.
3. The loop, repeated after every step:

   ```powershell
   ruff format app tests migrations
   ruff check app tests migrations
   python -m pytest -q
   ```

**Final state:** Ruff reports *All checks passed*, and all 58 tests pass.

---

## Step 17 — Documentation

- **OpenAPI (`/docs`, `/redoc`)**
  - The long description and tag descriptions come from `core/openapi.py`.
  - Every route has a summary, a description and documented errors.
  - Every schema field has a description and examples.
  - The worked example is pre-filled.
- **`README.md`** covers setup, configuration, API conventions, the pricing
  rules and the layout.
- **`docs/TECHNICAL_REFERENCE.md`** covers every file and function, and
  who calls what.
- **`docs/BUILD_GUIDE.md`** is this file.

---

## Adding the next feature (recipe)

Example: appointments.

1. `app/appointments/models.py`: table with `business_id` and
   `TimestampMixin`. Import it in `app/db/registry.py`.
2. `policy.py` for any pure rules, with unit tests first.
3. `schemas.py`: create/update/read models using the `core.schemas` field
   types.
4. `service.py`: functions taking `(session, business, …)`. Filter by
   `business.id`, raise `core.errors` exceptions, call `record_activity`, and
   commit once. Add new `ActivityAction` values.
5. `router.py`
   - Take `CurrentBusiness` and `SessionDep`.
   - Give every route a summary, a description and `error_responses(...)`.
   - Use a unique function name; it becomes the `operationId`.
   - Add a tag in `core/openapi.py`.
6. Include the router in `app/api.py`.
7. `alembic revision --autogenerate -m "add appointments"`, review the file,
   then `alembic upgrade head`.
8. Add API tests in `tests/api/`, and run the quality loop.

## Adding authentication later

The data model is already ready for it:

1. Add an accounts table, and change `business/dependencies.py`
   `get_current_business` to resolve the business from the token or device
   instead of `get_business(session)`.
2. Protect `/v1/admin/*` with an admin dependency on the admin router.
3. Create the business on sign-up with the existing `POST /v1/businesses`
   path (`copy_quote_defaults` is already used there).

No service, schema or table needs to change: every query is already scoped
by `business.id`.
