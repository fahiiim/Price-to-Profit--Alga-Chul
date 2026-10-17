"""Text and metadata for the generated API documentation (/docs, /redoc)."""

from fastapi.routing import APIRoute

API_DESCRIPTION = """
Backend for **Price to Profit**, the quote, pricing and invoice app for hair
extension stylists.

A stylist builds a quote from hair (bought in packs and sold by the gram with a
markup), labour hours, services, materials and fees. The API prices it, keeps
the history, turns accepted quotes into invoices and renders branded PDFs. It
also shows the stylist what they really earn: cost, profit and profit per hour.

## How to read this API

* **Base path**: every business endpoint lives under `/v1`.
* **Which business**: this is a multi-tenant API. `POST /v1/businesses`
  creates a studio (first-launch setup). Store the returned `id` and send
  it as **`X-Business-Id`** on every later request (quotes, invoices,
  library, dashboard, profile, logo). Login is not in this version; the
  header is the stand-in for the account.
* **Money** is exact. Send amounts as strings or numbers with up to two
  decimals (`"350.00"` or `350`). Amounts in responses are **strings** such as
  `"2104.00"` so no precision is lost.
* **Dates** are `YYYY-MM-DD`; timestamps are ISO 8601 in UTC.
* **Lists** are paginated with `limit` (1-100, default 20) and `offset`, and
  return `{items, total, limit, offset}`.
* **Partial updates** use `PATCH`: only the fields you send change.
* **Errors** always look like this:

```json
{"error": {"code": "not_found", "message": "Quote 42 was not found."}}
```

| code | HTTP | meaning |
| --- | --- | --- |
| `validation_error` | 422 | The body or query is malformed (see `details`). |
| `business_rule_violation` | 422 | Valid input that breaks a rule. |
| `pricing_error` | 422 | A value the pricing engine cannot work with. |
| `not_found` | 404 | The record does not exist. |
| `conflict` | 409 | Not allowed in the record's current state. |
| `file_too_large` / `unsupported_file_type` | 413 / 415 | Logo upload problems. |

## Typical flow

1. `POST /v1/businesses` on first launch (identity, contact, quote defaults),
   then `PUT /v1/business/logo`. Send `X-Business-Id` after that.
2. `POST /v1/library` to save hair products, services and materials.
3. `POST /v1/quotes/preview` while the stylist edits, for live totals.
4. `POST /v1/quotes` to save, `PATCH /v1/quotes/{id}/status` as it progresses.
5. `GET /v1/quotes/{id}/pdf` to share with the client.
6. `POST /v1/quotes/{id}/invoice`, then `PATCH /v1/invoices/{id}/status` as
   payments arrive.

## Scope

There is **no login, registration or subscription** handling in this version.
Many businesses can exist; the app identifies itself with `X-Business-Id`.
Admin endpoints are not protected yet.
"""

OPENAPI_TAGS = [
    {
        "name": "Health",
        "description": "Liveness and readiness probes for hosting platforms.",
    },
    {
        "name": "App config",
        "description": "Public configuration the mobile app reads on launch.",
    },
    {
        "name": "Business",
        "description": (
            "Create a studio on first launch (`POST /v1/businesses`), then "
            "read and update the current profile (`X-Business-Id`): name, "
            "tagline, contact details, logo, payment link, numbering and "
            "pricing defaults."
        ),
    },
    {
        "name": "Library",
        "description": (
            "Saved hair products, labour rates, services, materials and fees "
            "that pre-fill quote lines."
        ),
    },
    {
        "name": "Quotes",
        "description": (
            "Build, price, save, search and track quotes. All prices are "
            "calculated by the server; see **Price lines without saving** for "
            "the full calculation."
        ),
    },
    {
        "name": "Invoices",
        "description": "Create invoices from quotes and record payments.",
    },
    {
        "name": "Documents",
        "description": (
            "Branded A4 PDFs: the client quote, the invoice and the internal "
            "cost sheet."
        ),
    },
    {
        "name": "Dashboard",
        "description": "Figures for the app home screen.",
    },
    {
        "name": "Admin",
        "description": (
            "The owner's web dashboard: overview, business usage, platform "
            "quote defaults, app settings and the activity log. "
            "**Not protected yet.**"
        ),
    },
]


def operation_id(route: APIRoute) -> str:
    """Use the endpoint function name, e.g. `create_new_quote`.

    Gives clean method names to generated API clients. Endpoint function
    names are therefore unique across the whole application.
    """
    return route.name
