from typing import Any

from fastapi.testclient import TestClient

from app.platform.models import DEFAULT_INVOICE_TERMS, DEFAULT_QUOTE_TERMS


def test_dashboard_counts_invoiced_profit(
    client: TestClient, created_quote: dict[str, Any]
) -> None:
    invoice = client.post(f"/v1/quotes/{created_quote['id']}/invoice").json()
    client.patch(
        f"/v1/invoices/{invoice['id']}/status", json={"status": "deposit_paid"}
    )

    body = client.get("/v1/dashboard").json()
    period = body["period"]
    assert period["quotes_created"] == 1
    assert period["quoted_value"] == "2104.00"
    assert period["quotes_won"] == 1
    assert period["win_rate_percent"] == "100.00"
    assert period["invoiced_value"] == "2104.00"
    assert period["collected"] == "600.00"
    assert period["profit"] == "1240.00"
    assert period["profit_per_hour"] == "354.29"
    assert body["outstanding"] == {"unpaid_invoices": 1, "amount_due": "1504.00"}
    assert body["quote_status_counts"]["invoiced"] == 1
    assert len(body["recent_quotes"]) == 1


def test_dashboard_rejects_inverted_range(client: TestClient) -> None:
    response = client.get(
        "/v1/dashboard", params={"date_from": "2026-10-10", "date_to": "2026-10-01"}
    )
    assert response.status_code == 422


def test_admin_overview_and_activity(
    client: TestClient, created_quote: dict[str, Any]
) -> None:
    overview = client.get("/v1/admin/overview").json()
    assert overview["all_time"]["quotes_created"] == 1
    assert overview["recent_activity"][0]["action"] == "quote.created"

    activity = client.get("/v1/admin/activity", params={"entity_type": "quote"})
    assert activity.json()["total"] == 1

    detail = client.get("/v1/admin/business").json()
    assert detail["profile"]["currency"] == "AED"


def test_admin_defaults_can_be_replaced_and_applied(client: TestClient) -> None:
    defaults = client.get("/v1/admin/defaults").json()
    defaults.pop("updated_at")
    defaults.update({"hourly_rate": "250.00", "currency": "USD"})

    saved = client.put("/v1/admin/defaults", json=defaults)
    assert saved.status_code == 200
    assert client.get("/v1/business").json()["hourly_rate"] == "180.00"

    applied = client.post("/v1/admin/defaults/apply").json()
    assert applied["hourly_rate"] == "250.00"
    assert applied["currency"] == "USD"
    assert applied["quote_terms"] == DEFAULT_QUOTE_TERMS
    assert applied["invoice_terms"] == DEFAULT_INVOICE_TERMS


def test_admin_app_settings_feed_app_config(client: TestClient) -> None:
    response = client.patch(
        "/v1/admin/settings",
        json={"maintenance_mode": True, "maintenance_message": "Back at 5pm"},
    )
    assert response.status_code == 200
    config = client.get("/v1/app-config").json()
    assert config["maintenance_mode"] is True
    assert config["maintenance_message"] == "Back at 5pm"


def test_openapi_documents_every_route(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()
    for path in schema["paths"].values():
        for operation in path.values():
            assert operation.get("summary"), operation["operationId"]
            assert operation.get("tags"), operation["operationId"]
