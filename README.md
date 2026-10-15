# Price to Profit — Backend API

Backend for **Price to Profit**, a quoting and invoicing app for hair extension
stylists. A stylist builds a quote from hair, labour, services, materials and
fees; the API prices it exactly, shows the profit behind it, turns it into an
invoice, tracks payment and renders branded PDFs.

| | |
|---|---|
| Language | Python 3.12 |
| Framework | FastAPI (Pydantic v2) |
| Database | SQLite through SQLAlchemy 2 (sync) + Alembic migrations |
| PDFs | ReportLab |
| Quality | Ruff (PEP 8 + import order + modern Python), pytest |

There is **no login, registration or subscription** in this version. The API
serves a single business profile; every table already carries `business_id`
so per-account access can be added later without reshaping the data
(see [Scope](#scope)).

More documentation:

- [`docs/TECHNICAL_REFERENCE.md`](docs/TECHNICAL_REFERENCE.md) — every folder,
  file, class and function, and how data moves between them.
- [`docs/BUILD_GUIDE.md`](docs/BUILD_GUIDE.md) — the order the backend was
  built in, step by step, and how each layer connects to the previous one.
- Interactive API docs at `/docs` (Swagger UI) and `/redoc` once the server is
  running.

---

## Quick start

```powershell
# 1. Create and activate a virtual environment (Python 3.12)
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1          # macOS/Linux: source .venv/bin/activate

# 2. Install the app with development tools
pip install -e ".[dev]"

# 3. (Optional) copy the example environment file
copy .env.example .env                 # macOS/Linux: cp .env.example .env

# 4. Create the database schema
alembic upgrade head

# 5. Run the API
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000/docs>. On first start the API seeds the platform
settings row and the business profile, so every endpoint works immediately.

### Try the worked example

`POST /v1/quotes/preview` and `POST /v1/quotes` come pre-filled in Swagger UI
with the worked example below. It prices to:

| Figure | Value |
|---|---|
| Subtotal (before VAT) | 2,005.00 |
| VAT 5 % (shipping is not taxable) | 99.00 |
| **Total** | **2,104.00** |
| Deposit / balance | 600.00 / 1,504.00 |
| Cost | 765.00 |
| **Profit** | **1,240.00** (61.85 % margin, 354.29 per labour hour) |

---

## Configuration

All settings are optional and read from environment variables (or `.env`)
with the `PTP_` prefix.

| Variable | Default | Purpose |
|---|---|---|
| `PTP_APP_NAME` | `Price to Profit API` | Title in the API docs |
| `PTP_APP_VERSION` | `0.1.0` | Version in the API docs and `/health/live` |
| `PTP_ENVIRONMENT` | `local` | Label shown in `/health/live` |
| `PTP_DATABASE_URL` | `sqlite:///<project>/price_to_profit.db` | SQLAlchemy URL |
| `PTP_MEDIA_DIR` | `<project>/media` | Where uploaded logos are stored |
| `PTP_MAX_LOGO_BYTES` | `2000000` | Largest accepted logo upload |
| `PTP_CORS_ORIGINS` | `["*"]` | Allowed origins, as a JSON list |

---

## API at a glance

All business endpoints live under `/v1`. Every endpoint has a summary, a long
description, request examples and its documented error responses in `/docs`.

| Area | Endpoints | What it does |
|---|---|---|
| Health | `GET /health/live`, `GET /health/ready` | Process and database checks |
| App config | `GET /v1/app-config` | Support contacts, legal links, version gate, maintenance mode |
| Business | `GET/PATCH /v1/business`, `PUT/GET/DELETE /v1/business/logo` | Branding, contact details, tax, rates, deposit and numbering defaults |
| Library | `GET/POST /v1/library`, `GET/PATCH/DELETE /v1/library/{id}` | Saved hair products, services, materials and fees |
| Quotes | `POST /v1/quotes/preview`, `GET/POST /v1/quotes`, `GET/PATCH/DELETE /v1/quotes/{id}`, `PATCH /v1/quotes/{id}/status`, `POST /v1/quotes/{id}/duplicate` | Live pricing, CRUD, status workflow, search |
| Invoices | `POST /v1/quotes/{id}/invoice`, `GET /v1/invoices`, `GET/DELETE /v1/invoices/{id}`, `PATCH /v1/invoices/{id}/status` | Invoice a quote, record payments |
| Documents | `GET /v1/quotes/{id}/pdf`, `GET /v1/quotes/{id}/cost-sheet/pdf`, `GET /v1/invoices/{id}/pdf` | Branded PDFs (`?download=true` to force a download) |
| Dashboard | `GET /v1/dashboard` | Period figures, money outstanding, status counts, recent quotes |
| Admin | `/v1/admin/overview`, `/business`, `/defaults`, `/defaults/apply`, `/settings`, `/activity` | Owner dashboard: platform defaults, app settings, activity log |

### Conventions

- **Money** is exact. Amounts are sent and returned as **decimal strings**
  (`"2104.00"`); numbers are accepted on input and rounded half-up to two
  decimal places. Floats are never used for money.
- **Lists** are paginated with `limit` (1–100, default 20) and `offset`, and
  return `{"items": [...], "total": n, "limit": l, "offset": o}`.
- **Creates** return `201 Created` with a `Location` header; **deletes** return
  `204 No Content`.
- **Errors** always use one envelope:

  ```json
  {"error": {"code": "not_found", "message": "Quote 7 was not found.", "details": null}}
  ```

  | HTTP | `code` | When |
  |---|---|---|
  | 404 | `not_found` | The record does not exist |
  | 409 | `conflict` | The record's state forbids the action (e.g. editing an invoiced quote) |
  | 413 | `file_too_large` | Logo upload over the size limit |
  | 415 | `unsupported_file_type` | Logo is not PNG, JPEG or WebP |
  | 422 | `validation_error` | Request body or query failed validation (`details` lists each field) |
  | 422 | `business_rule_violation` | Valid shape, but breaks a rule (e.g. a hair line without grams) |
  | 422 | `pricing_error` | The pricing engine rejected the numbers |

### Quote and invoice lifecycle

```text
          ┌──────────── draft ◄────────────┐
          ▼               ▲                │
        sent ◄────────────┤             declined
          │               │                ▲
          ▼               │                │
       accepted ──────────┴────────────────┘
          │
          ▼  POST /v1/quotes/{id}/invoice   (also allowed from draft or sent)
       invoiced  ── locked: no edits, no status changes
          │
          ▼
   invoice: unpaid → deposit_paid → paid      (any order; amount_paid follows)
```

Deleting an invoice moves its quote back to `accepted`, so it can be edited
and invoiced again.

---

## How pricing works

The pricing engine (`app/pricing`) is pure Python with no framework imports.
Each line is rounded half-up to 2 decimals, and totals are summed from the
rounded lines, so the PDF always adds up.

| Line kind | Price | Cost |
|---|---|---|
| `hair` | cost × (1 + markup % / 100) | whole packs: ⌈grams ÷ grams per pack⌉ × pack price; otherwise grams × (pack price ÷ grams per pack) |
| `labour` | hours × hourly rate | 0 (time, not money) |
| `service`, `material`, `fee` | quantity × unit price | quantity × unit cost |

- **Subtotal** = sum of line prices. **Tax** = tax rate % of the *taxable*
  lines only. **Total** = subtotal + tax.
- **Deposit** = a percent of the total or a fixed amount, capped at the total.
  **Balance** = total − deposit.
- **Profit** = subtotal − cost (tax is passed on, not earned).
  **Margin** = profit ÷ subtotal. **Profit per hour** = profit ÷ labour hours.

Missing line values are filled from, in order: the line itself, the linked
library item, then the business defaults (hourly rate, markup, whole packs).

---

## Development

```powershell
# Tests (unit + API, each test uses a fresh in-memory database)
python -m pytest -q

# Lint and format (PEP 8, import order, modern Python idioms)
ruff format app tests migrations
ruff check app tests migrations

# New migration after changing a model
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

### Project layout

```text
app/
├── main.py            ASGI entry point (uvicorn app.main:app)
├── factory.py         create_app(): settings, database, handlers, routers
├── api.py             mounts every feature router under /v1
├── bootstrap.py       seeds the rows the app needs on start-up
├── health.py          /health/live and /health/ready
├── core/              config, clock, errors, error handlers, shared schemas,
│                      dependencies, OpenAPI text
├── db/                declarative base, session factory, exact column types
├── pricing/           pure pricing engine (no FastAPI/SQLAlchemy)
├── platform/          admin-owned defaults + mobile app config
├── activity/          append-only activity log
├── business/          business profile, logo, document numbering
├── library/           saved products, services, materials, fees
├── quotes/            quote lifecycle, line resolution, search
├── invoices/          invoices from quotes, payment status
├── documents/         ReportLab PDFs (quote, invoice, cost sheet) + fonts
├── dashboard/         SQL aggregates for the home screen
└── admin/             owner dashboard endpoints
migrations/            Alembic environment and versions
tests/                 unit/ (pure logic) and api/ (HTTP end to end)
docs/                  technical reference and build guide
```

Each feature folder follows the same shape: `models.py` (tables),
`schemas.py` (request/response models), `service.py` (use cases),
`router.py` (HTTP), plus `policy.py`/`rules.py` for pure business rules where
a feature has them.

---

## Scope

Not included in this version, by design:

- Authentication, registration, subscriptions and billing.
- Multiple businesses. `CurrentBusiness` (`app/business/dependencies.py`) is
  the single place that decides which business a request belongs to; it
  always returns business `1` today and is where a token or device lookup
  would go later.
- Sending quotes or invoices by email/WhatsApp; the app shares the PDFs.
