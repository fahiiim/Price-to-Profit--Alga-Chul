from typing import Any

from fastapi.testclient import TestClient

EXPECTED_TOTALS = {
    "subtotal": "2005.00",
    "taxable_amount": "1980.00",
    "tax_amount": "99.00",
    "total": "2104.00",
    "deposit_amount": "600.00",
    "balance_due": "1504.00",
    "total_cost": "765.00",
    "profit": "1240.00",
    "labour_hours": "3.50",
    "profit_per_hour": "354.29",
    "margin_percent": "61.85",
}


def test_preview_prices_the_worked_example(
    client: TestClient, quote_payload: dict[str, Any]
) -> None:
    body = {key: quote_payload[key] for key in ("lines", "deposit")}
    response = client.post("/v1/quotes/preview", json=body)

    assert response.status_code == 200
    preview = response.json()
    assert preview["totals"] == EXPECTED_TOTALS
    hair = preview["lines"][0]
    assert hair["packs_needed"] == 2
    assert hair["leftover_grams"] == "30.00"
    assert client.get("/v1/quotes").json()["total"] == 0


def test_create_quote(created_quote: dict[str, Any]) -> None:
    assert created_quote["number"] == "Q-0001"
    assert created_quote["status"] == "draft"
    assert created_quote["totals"] == EXPECTED_TOTALS
    assert [line["position"] for line in created_quote["lines"]] == [1, 2, 3, 4, 5]
    assert created_quote["valid_until"] is not None


def test_lines_use_library_and_business_defaults(client: TestClient) -> None:
    item = client.post(
        "/v1/library",
        json={
            "kind": "hair",
            "name": "Keratin bonds 22in",
            "grams_per_pack": "50",
            "pack_price": "200",
        },
    ).json()
    response = client.post(
        "/v1/quotes",
        json={
            "client": {"name": "Mona"},
            "lines": [
                {"library_item_id": item["id"], "grams_required": "120"},
                {"kind": "labour", "hours": "2"},
            ],
        },
    )
    assert response.status_code == 201
    hair, labour = response.json()["lines"]
    assert hair["kind"] == "hair"
    assert hair["description"] == "Keratin bonds 22in"
    assert hair["packs_needed"] == 3
    assert hair["markup_percent"] == "60.00"
    assert hair["price"] == "960.00"
    assert labour["hourly_rate"] == "180.00"
    assert labour["price"] == "360.00"


def test_missing_line_values_point_at_the_line(client: TestClient) -> None:
    response = client.post(
        "/v1/quotes",
        json={"client": {"name": "Mona"}, "lines": [{"kind": "hair"}]},
    )
    assert response.status_code == 422
    assert response.json()["error"]["message"].startswith("Line 1 (hair)")


def test_update_reprices(client: TestClient, created_quote: dict[str, Any]) -> None:
    response = client.patch(
        f"/v1/quotes/{created_quote['id']}",
        json={"tax_rate_percent": "0", "title": "Half head"},
    )
    body = response.json()
    assert response.status_code == 200
    assert body["title"] == "Half head"
    assert body["totals"]["tax_amount"] == "0.00"
    assert body["totals"]["total"] == "2005.00"
    assert len(body["lines"]) == 5


def test_status_flow(client: TestClient, created_quote: dict[str, Any]) -> None:
    url = f"/v1/quotes/{created_quote['id']}/status"
    sent = client.patch(url, json={"status": "sent"}).json()
    assert sent["status"] == "sent"
    assert sent["sent_at"] is not None

    declined = client.patch(url, json={"status": "declined"})
    assert declined.json()["status"] == "declined"

    invalid = client.patch(url, json={"status": "accepted"})
    assert invalid.status_code == 409
    assert invalid.json()["error"]["code"] == "conflict"


def test_list_search_and_filter(
    client: TestClient, quote_payload: dict[str, Any]
) -> None:
    client.post("/v1/quotes", json=quote_payload)
    quote_payload["client"] = {"name": "Layla Hassan"}
    second = client.post("/v1/quotes", json=quote_payload).json()
    client.patch(f"/v1/quotes/{second['id']}/status", json={"status": "sent"})

    assert client.get("/v1/quotes").json()["total"] == 2
    assert client.get("/v1/quotes", params={"search": "layla"}).json()["total"] == 1
    assert client.get("/v1/quotes", params={"status": "sent"}).json()["total"] == 1
    page = client.get("/v1/quotes", params={"limit": 1}).json()
    assert len(page["items"]) == 1
    assert page["items"][0]["number"] == "Q-0002"


def test_duplicate(client: TestClient, created_quote: dict[str, Any]) -> None:
    response = client.post(f"/v1/quotes/{created_quote['id']}/duplicate")
    copy = response.json()
    assert response.status_code == 201
    assert copy["number"] == "Q-0002"
    assert copy["status"] == "draft"
    assert copy["totals"] == created_quote["totals"]
    assert copy["appointment_date"] is None


def test_delete(client: TestClient, created_quote: dict[str, Any]) -> None:
    assert client.delete(f"/v1/quotes/{created_quote['id']}").status_code == 204
    assert client.get(f"/v1/quotes/{created_quote['id']}").status_code == 404
